import functools
import os
import time
import traceback

from deta import Deta
from deta.base import FetchResponse


class TestFailure(Exception):
    pass


def test(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            raise TestFailure from e

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

    def run(self):
        details = {}
        start_time = time.perf_counter()
        try:
            for test in self.tests:
                test()
            passed = True
        except Exception:
            passed = False
            details['error'] = {'traceback': traceback.format_exc()}
        result = self.save_result(passed, time.perf_counter() - start_time, details)
        self.close()
        return result

    def close(self):
        pass

    def save_result(self, result: bool, duration: float, details: dict):
        data = {
            'service': self.service,
            'region': self.region,
            'passed': result,
            'timestamp': int(time.time()),
            'duration': round(duration, 10),
            'details': details,
        }
        results_base = self.deta.Base(f'results-{self.service}')
        key = f"{data['timestamp']}-{data['service']}-{data['region']}"
        results_base.put(data, key=key, expire_in=60 * 60 * 24 * 1)
        return data


class BaseTests(Tests):
    def __init__(self):
        super().__init__('base')
        self.test_base = self.deta.Base('test-base')
        self.tests = [
            self.test_put,
            self.test_insert,
            self.test_get,
            self.test_delete,
            self.test_fetch,
            self.test_update,
        ]

    def close(self):
        items = self.test_base.fetch().items
        for item in items:
            self.test_base.delete(item['key'])

    @test
    def test_put(self):
        item = {'key': 'test_put', 'content': 'testing put'}
        assert self.test_base.put(item) == item

    @test
    def test_insert(self):
        item = {'key': 'test_insert', 'content': 'testing insert'}
        assert self.test_base.insert(item) == item

    @test
    def test_get(self):
        item = {'key': 'test_get', 'content': 'testing get'}
        self.test_base.put(item)
        assert self.test_base.get(item['key']) == item

    @test
    def test_delete(self):
        item = {'key': 'test_delete', 'content': 'testing delete'}
        self.test_base.delete(item['key'])

    @test
    def test_fetch(self):
        items = [
            {'key': 'test_fetch', 'content': 'testing fetch'},
            {'key': 'test_fetch2', 'content': 'also testing fetch'},
        ]
        self.test_base.put_many(items)
        resp = self.test_base.fetch({'content?contains': 'fetch'})
        expected = FetchResponse(2, None, items)
        assert resp == expected

    @test
    def test_update(self):
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
            # self.test_put,
            # self.test_delete,
            # self.test_list,
            self.test_all,
        ]

    def close(self):
        names = self.test_drive.list()['names']
        if names:
            self.test_drive.delete_many(names)

    # @test
    # def test_put(self):
    #     item = {'name': 'test_put.txt', 'content': 'testing put'}
    #     assert self.drive.put(item['name'], item['content']) == item['name']
    #     assert self.drive.get(item['name']).read().decode() == item['content']

    # @test
    # def test_delete(self):
    #     item = {'name': 'test_delete.txt', 'content': 'testing delete'}
    #     self.drive.put(item['name'], item['content'])
    #     assert self.drive.delete(item['name']) == item['name']
    #     # assert self.drive.get(item['name']) is None

    # @test
    # def test_list(self):
    #     item = {'name': 'b/c', 'content': 'testing list'}
    #     self.drive.put(item['name'], item['content'])
    #     assert item['name'] in self.drive.list()['names']

    # combined tests to avoid timeouts
    @test
    def test_all(self):
        item = {'name': 'test_all.txt', 'content': 'testing all'}
        assert self.test_drive.put(item['name'], item['content']) == item['name']
        assert self.test_drive.get(item['name']).read().decode() == item['content']
        assert item['name'] in self.test_drive.list()['names']
        assert self.test_drive.delete(item['name']) == item['name']


class MicroTests(Tests):
    def __init__(self):
        super().__init__('micro')
        self.tests = []
        # placeholder micro test
