import os
import time

from deta import Deta
from fastapi import FastAPI, HTTPException, Request, Header, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import Result

token = os.getenv('DETA_PROJECT_KEY_DASHBOARD')
app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')
deta = Deta(token)
results_base = deta.Base('results')


@app.get('/', response_class=HTMLResponse)
async def root(request: Request):
    results = results_base.fetch(query={'timestamp?gt': int(time.time() - (60 * 60))}).items
    return templates.TemplateResponse(
        'index.html',
        {'request': request, 'results': results},
    )


@app.get('/api')
async def api(request: Request):
    return templates.TemplateResponse('api.html', {'request': request})


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
    return [Result.parse_obj(result) for result in results]


@app.post('/api/save', status_code=201)
async def api_save(result: Result, authorization: str = Header(default='')):
    if authorization != token:
        raise HTTPException(status_code=401)
    key = f"{result.timestamp}-{result.service}-{result.region}"
    results_base.put(result.dict(), key=key, expire_in=60 * 60 * 24 * 90)


@app.exception_handler(404)
async def not_found_handler(request: Request, exception):
    return templates.TemplateResponse('404.html', {'request': request})
