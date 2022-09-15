import os

from deta import App, Deta
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import RedirectResponse
from requests_futures.sessions import FuturesSession
from tests import BaseTests, DriveTests, MicroTests

from models import Result

app = App(FastAPI())
deta = Deta()
results_base = deta.Base('results')
tests = {
    'base': BaseTests,
    'drive': DriveTests,
    'micro': MicroTests,
}


@app.get('/')
async def root():
    return RedirectResponse('https://service-status.deta.dev/')


@app.get('/api/results', response_model=list[Result])
async def api_results(response: Response, service: str = '', region: str = ''):
    query = {}
    if service:
        query['service'] = service
    if region:
        query['region'] = region
    results = results_base.fetch(query=query).items
    for result in results:
        del result['key']
    response.headers['Access-Control-Allow-Origin'] = '*'  # FIXME: temporary
    return results


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
