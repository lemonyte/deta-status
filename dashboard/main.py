from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')


@app.get('/', response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/api')
async def api(request: Request):
    return templates.TemplateResponse('api.html', {'request': request})


@app.exception_handler(404)
async def not_found_handler(request: Request, _):
    return templates.TemplateResponse('404.html', {'request': request})
