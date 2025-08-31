from __future__ import annotations

from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db.base import init_db

app = FastAPI(title="Random Contest Bot WebApp")

# Static and templates
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
templates = Jinja2Templates(directory="app/web/templates")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health", response_class=HTMLResponse)
def health():
    return "OK"


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})