from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator
import os

from app.config import settings


class Base(DeclarativeBase):
    pass


def _create_engine():
    database_url = settings.DATABASE_URL
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        # Ensure directory exists
        path = database_url.replace("sqlite:///", "").replace("sqlite:////", "/")
        data_dir = os.path.dirname(path)
        if data_dir and not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
    return create_engine(database_url, connect_args=connect_args, pool_pre_ping=True, future=True)


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db() -> None:
    # Import models to register metadata
    from app.db import models  # noqa: F401
    Base.metadata.create_all(bind=engine) 