"""Точка сборки FastAPI-приложения."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine
from app.services.mail_sender import MailSender
from app.services.worker import Worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # MVP: создаём таблицы, если их нет (позже заменит Alembic).
    setup_logging()
    Base.metadata.create_all(engine)

    settings = get_settings()
    worker = Worker(settings, MailSender(settings))
    app.state.worker = worker
    worker.start()

    yield

    worker.stop()


app = FastAPI(title="vibe_mail API", version="0.1.0", lifespan=lifespan)
