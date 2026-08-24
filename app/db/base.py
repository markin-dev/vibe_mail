"""Базовый класс для всех ORM-моделей SQLAlchemy."""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Общий предок декларативных моделей."""
