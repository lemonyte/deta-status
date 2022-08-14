import functools
import os
import time

from deta import Deta
from deta.base import FetchResponse
from dotenv import load_dotenv

load_dotenv()


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
    def __init__(self, service: str, test_name: str, results_base_name: str):
        key = os.getenv('DETA_PROJECT_KEY')
        if not key:
            raise ValueError('no project key provided')
        if not service:
            raise ValueError('no service name provided')
        if not test_name:
            raise ValueError('no test component name provided')
        if not results_base_name:
            raise ValueError('no results base name provided')
        self.service = service
        self.test_name = test_name
        self.tests = []
        self.deta = Deta(key)
        self.results_base = self.deta.Base(results_base_name)

    def run(self):
        if not self.tests:
            raise NotImplementedError
        try:
            for test in self.tests:
                test()
            self.save_result(True)
            self.close()
        except Exception:
            self.save_result(False)
            self.close()
            raise

    def close(self):
        raise NotImplementedError

    def save_result(self, result: bool):
        if not self.service:
            raise NotImplementedError
        self.results_base.put(
            {
                'key': f'{int(time.time())}-{self.service}',
                'service': self.service,
                'passed': result,
                'timestamp': int(time.time()),
            }
        )


class DetaBaseTests(Tests):
    def __init__(self, test_name: str, results_base_name: str):
        super().__init__('base', test_name, results_base_name)
        self.test_base = self.deta.Base(self.test_name)
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
        self.test_base.client.close()

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


class DetaDriveTests(Tests):
    def __init__(self, test_name: str, results_base_name: str):
        super().__init__('drive', test_name, results_base_name)
        self.test_drive = self.deta.Drive(self.test_name)
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
