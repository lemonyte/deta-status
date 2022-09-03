import os

from deta import App
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from requests_futures.sessions import FuturesSession
from tests import BaseTests, DriveTests, MicroTests

app = App(FastAPI())
tests = {
    'base': BaseTests,
    'drive': DriveTests,
    'micro': MicroTests,
}


@app.get('/')
async def root():
    return RedirectResponse('https://service-status.deta.dev/')


@app.get('/{test}')
async def test(test: str):
    if test not in tests.keys():
        raise HTTPException(status_code=404)
    return tests[test]().run()


@app.lib.cron()
def cron(event: str):
    path = os.getenv('DETA_PATH')
    session = FuturesSession()
    for test in tests.keys():
        session.get(f'https://{path}.deta.dev/{test}')
