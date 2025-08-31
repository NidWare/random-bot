from __future__ import annotations

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging

from app.db.base import init_db, get_session
from app.services.participant_service import ParticipantService

logger = logging.getLogger(__name__)

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


@app.post("/participate")
async def participate(
    telegram_user_id: int = Form(...),
    username: str = Form(None),
    first_name: str = Form(None),
    last_name: str = Form(None),
):
    """Fallback endpoint for participant registration when Mini App doesn't work"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        service = ParticipantService(session)
        logger.info("Web endpoint: Upserting participant id=%s username=%s", telegram_user_id, username)
        participant = service.submit_participation(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=None,
            is_premium=None,
            extra_data={"source": "web_fallback"},
        )
        return JSONResponse({"success": True, "message": "Участник зарегистрирован", "participant_id": participant.id})
    except Exception as e:
        logger.error("Failed to register participant: %s", e)
        raise HTTPException(status_code=500, detail="Ошибка регистрации участника")
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass