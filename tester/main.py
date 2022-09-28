import asyncio
import os

import httpx
from deta import App, Deta  # type: ignore
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse

from tests import BaseTests, DriveTests, MicroTests
from models import Result

app = App(FastAPI())
deta = Deta()
tests = {
    'base': BaseTests,
    'drive': DriveTests,
    'micro': MicroTests,
}


@app.get('/')
async def root():
    return RedirectResponse('https://service-status.deta.dev/')


@app.get('/results/{service}', response_model=list[Result])
async def api_results(response: Response, service: str):
    if service not in tests.keys():
        raise HTTPException(status_code=400, detail='invalid service')
    results_base = deta.Base(f'results-{service}')
    results = results_base.fetch().items
    for result in results:
        del result['key']
    response.headers['Access-Control-Allow-Origin'] = '*'  # FIXME: temporary
    return results


@app.get('/test/{service}')
async def test(service: str):
    if service not in tests.keys():
        raise HTTPException(status_code=404)
    return tests[service]().run()


@app.get('/ping')
async def ping():
    return 'pong'


async def start_tests():
    path = os.getenv('DETA_PATH')
    async with httpx.AsyncClient() as client:
        for service in tests.keys():
            _ = client.get(f'https://{path}.deta.dev/test/{service}')


@app.lib.cron()  # type: ignore
def cron(event: str):
    asyncio.run(start_tests())
