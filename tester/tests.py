import asyncio
import functools
import os
import time

import httpx
from deta import Deta
from deta.base import FetchResponse

from models import TestResult, TestResults


def test(func):
    @functools.wraps(func)
    async def decorator(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            details = await func(*args, **kwargs)
            if details is None:
                details = {}
            elif not isinstance(details, dict):
                details = {'value': details}
            passed = True
        except Exception as e:
            passed = False
            details = {'error': repr(e)}
        duration = time.perf_counter() - start_time
        return TestResult(
            name=func.__name__.lstrip('test_'),
            passed=passed,
            duration=duration,
            details=details
        )

    return decorator


class Tests:
    def __init__(self, service: str):
        if not service:
            raise ValueError("service name must be a non-empty string")
        region = os.getenv('REGION')
        if not region:
            raise ValueError("no region provided")
        self.service = service
        self.region = region
        self.tests = []
        self.deta = Deta()

    async def run(self):
        start_time = time.perf_counter()
        test_results: list[TestResult] = await asyncio.gather(*map(lambda t: t(), self.tests))
        duration = time.perf_counter() - start_time
        results = TestResults(
            tests={r.name: r for r in test_results},
            service=self.service,
            region=self.region,
            timestamp=int(time.time()),
            duration=duration,
        )
        await self.save_results(results)
        await self.close()
        return results

    async def close(self):
        pass

    async def save_results(self, results: TestResults):
        results_base = self.deta.Base(f'results-{self.service}')
        results_base.put(results.dict(), key=str(results.timestamp), expire_in=60 * 60 * 24 * 1)


class BaseTests(Tests):
    def __init__(self):
        super().__init__('base')
        self.test_base = self.deta.Base('test-base')
        self.tests = [
            self.test_ping,
            self.test_put,
            self.test_insert,
            self.test_get,
            self.test_delete,
            self.test_fetch,
            self.test_update,
        ]

    async def close(self):
        items = self.test_base.fetch().items
        for item in items:
            self.test_base.delete(item['key'])

    @test
    async def test_ping(self):
        response = httpx.get('https://database.deta.sh')
        return {'response_time': response.elapsed.total_seconds()}

    @test
    async def test_put(self):
        item = {'key': 'test_put', 'content': 'testing put'}
        assert self.test_base.put(item) == item

    @test
    async def test_insert(self):
        item = {'key': 'test_insert', 'content': 'testing insert'}
        assert self.test_base.insert(item) == item

    @test
    async def test_get(self):
        item = {'key': 'test_get', 'content': 'testing get'}
        self.test_base.put(item)
        assert self.test_base.get(item['key']) == item

    @test
    async def test_delete(self):
        item = {'key': 'test_delete', 'content': 'testing delete'}
        self.test_base.delete(item['key'])

    @test
    async def test_fetch(self):
        items = [
            {'key': 'test_fetch', 'content': 'testing fetch'},
            {'key': 'test_fetch2', 'content': 'also testing fetch'},
        ]
        self.test_base.put_many(items)  # type: ignore
        resp = self.test_base.fetch({'content?contains': 'fetch'})
        expected = FetchResponse(2, None, items)
        assert resp == expected

    @test
    async def test_update(self):
        item = {'key': 'test_update', 'content': 'testing update'}
        self.test_base.put(item)
        self.test_base.update({'content': 'testing update (updated)'}, item['key'])
        expected = {'key': 'test_update', 'content': 'testing update (updated)'}
        assert self.test_base.get(item['key']) == expected


class DriveTests(Tests):
    def __init__(self):
        super().__init__('drive')
        self.test_drive = self.deta.Drive('test-drive')
        self.tests = [
            self.test_ping,
            # self.test_put,
            # self.test_delete,
            # self.test_list,
            self.test_all,
        ]

    async def close(self):
        names = self.test_drive.list()['names']  # type: ignore
        if names:
            self.test_drive.delete_many(names)

    @test
    async def test_ping(self):
        response = httpx.get('https://drive.deta.sh')
        return {'response_time': response.elapsed.total_seconds()}

    @test
    async def test_put(self):
        item = {'name': 'test_put.txt', 'content': 'testing put'}
        assert self.test_drive.put(item['name'], item['content']) == item['name']
        assert self.test_drive.get(item['name']).read().decode() == item['content']  # type: ignore

    @test
    async def test_delete(self):
        item = {'name': 'test_delete.txt', 'content': 'testing delete'}
        self.test_drive.put(item['name'], item['content'])
        assert self.test_drive.delete(item['name']) == item['name']
        # assert self.drive.get(item['name']) is None

    @test
    async def test_list(self):
        item = {'name': 'b/c', 'content': 'testing list'}
        self.test_drive.put(item['name'], item['content'])
        assert item['name'] in self.test_drive.list()['names']  # type: ignore

    # Combined tests to avoid timeouts.
    # US region is very slow, taking around 6 seconds to run 3 tests,
    # while Germany runs in under 2 seconds.
    @test
    async def test_all(self):
        item = {'name': 'test_all.txt', 'content': 'testing all'}
        assert self.test_drive.put(item['name'], item['content']) == item['name']
        assert self.test_drive.get(item['name']).read().decode() == item['content']  # type: ignore
        assert item['name'] in self.test_drive.list()['names']  # type: ignore
        assert self.test_drive.delete(item['name']) == item['name']


class MicroTests(Tests):
    def __init__(self):
        super().__init__('micro')
        self.tests = [
            self.test_ping,
        ]

    @test
    async def test_ping(self):
        path = os.getenv('DETA_PATH')
        response = httpx.get(f'https://{path}.deta.dev/ping')
        return {'response_time': response.elapsed.total_seconds()}
