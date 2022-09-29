import asyncio
import os

import httpx
from deta import App, Deta  # type: ignore
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse

from tests import BaseTests, DriveTests, MicroTests
from models import TestResults

app = App(FastAPI())
deta = Deta()
tests = {
    'base': BaseTests,
    'drive': DriveTests,
    'micro': MicroTests,
}


async def api_key_auth(request: Request):
    api_key = request.headers.get('X-API-Key')
    if api_key != os.getenv('DETA_PROJECT_KEY'):
        raise HTTPException(status_code=401)


@app.get('/')
async def root():
    return RedirectResponse('https://service-status.deta.dev/')


@app.get('/results/{service}', response_model=list[TestResults])
async def api_results(response: Response, service: str):
    if service not in tests.keys():
        raise HTTPException(status_code=400, detail='invalid service')
    results_base = deta.Base(f'results-{service}')
    results = results_base.fetch().items
    for result in results:
        del result['key']
    response.headers['Access-Control-Allow-Origin'] = '*'  # FIXME: temporary
    return results


@app.get('/test', response_model=list[TestResults], dependencies=[Depends(api_key_auth)])
async def run_tests():
    path = os.getenv('DETA_PATH')
    headers = {'X-API-Key': os.getenv('DETA_PROJECT_KEY') or ''}
    coros = []
    async with httpx.AsyncClient() as client:
        for service in tests.keys():
            coros.append(client.get(f'https://{path}.deta.dev/test/{service}', headers=headers))
        return await asyncio.gather(*coros)

    # The above code starts new instances of this Micro for each service test
    # by calling this Micro's '/test/{service}' endpoint.

    # Alternate way of running the 3 service tests,
    # without using any self-calling shenanigans, but prone to timeouts.

    # return await asyncio.gather(*map(test, tests.keys()))


@app.get('/test/{service}', response_model=TestResults, dependencies=[Depends(api_key_auth)])
async def test(service: str):
    if service not in tests.keys():
        raise HTTPException(status_code=404)
    return await tests[service]().run()


@app.get('/ping')
async def ping():
    return 'pong'


@app.lib.cron()
def cron(event: str):
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run_tests())
