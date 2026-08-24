"""Движок SQLAlchemy и фабрика сессий.

Одна БД (SQLite) используется и из HTTP-запросов, и из фонового воркера
в разных потоках, поэтому для SQLite отключаем check_same_thread.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()

_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_db():
    """Dependency для FastAPI: сессия на время запроса, затем закрытие."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
