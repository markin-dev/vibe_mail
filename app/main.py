"""Точка сборки FastAPI-приложения."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import attachments, campaigns, health, recipients
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.base import Base
from app.db.session import engine
from app.schemas.envelope import ApiEnvelope
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

cors_raw = get_settings().model_dump().get("CORS_ORIGINS") or "http://localhost:5173"
cors_origins = [origin.strip() for origin in cors_raw.split(",") if origin.strip()] or [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiEnvelope(status="error", result=None, error=str(exc.detail)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=ApiEnvelope(status="error", result=None, error=str(exc.errors())).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=ApiEnvelope(status="error", result=None, error="Внутренняя ошибка сервера").model_dump(),
    )


app.include_router(campaigns.router)
app.include_router(recipients.router)
app.include_router(attachments.router)
app.include_router(health.router)
