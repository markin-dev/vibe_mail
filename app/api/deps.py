"""Зависимости FastAPI: сессия БД и доступ к фоновому воркеру."""
from fastapi import Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.worker import Worker


def get_worker(request: Request) -> Worker:
    """Возвращает запущенный воркер из состояния приложения."""
    return request.app.state.worker
