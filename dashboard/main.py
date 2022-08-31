import os
import time

from deta import Deta
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import Result

load_dotenv()
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
def api(request: Request):
    return templates.TemplateResponse('api.html', {'request': request})


@app.post('/api/save', status_code=201)
async def api_save(result: Result, authorization: str = Header(default='')):
    if authorization != token:
        raise HTTPException(status_code=401)
    key = f"{result.timestamp}-{result.service}-{result.region}"
    results_base.put(result.dict(), key=key)


@app.exception_handler(404)
async def not_found_handler(request: Request, exception):
    return templates.TemplateResponse('404.html', {'request': request})
