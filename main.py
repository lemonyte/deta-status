# TODO
# frontend to view results
# investigate detalib App
# proper api responses

import os

from deta import App
from fastapi import FastAPI, Response, status
from requests_futures.sessions import FuturesSession


from tests import DetaBaseTests, DetaDriveTests, TestFailure

app = App(FastAPI())
results_base_name = 'results'


@app.get('/')
async def root():
    return {'message': 'Deta service status. Under construction.'}


@app.get('/micro')
async def micro_status():
    return {'message': 'Micro service is running'}


@app.get('/base')
async def base_status(response: Response):
    try:
        tests = DetaBaseTests('test-base', results_base_name)
        tests.run()
        return {'message': 'Base service is running'}
    except TestFailure:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {'message': 'Base service is not running'}


@app.get('/drive')
async def drive_status(response: Response):
    try:
        tests = DetaDriveTests('test-drive', results_base_name)
        tests.run()
        return {'message': 'Drive service is running'}
    except TestFailure:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {'message': 'Drive service is not running'}


@app.lib.cron()
def cron(event: str):
    session = FuturesSession()
    path = os.getenv('DETA_PATH')
    session.get(f'https://{path}.deta.dev/base')
    session.get(f'https://{path}.deta.dev/drive')
