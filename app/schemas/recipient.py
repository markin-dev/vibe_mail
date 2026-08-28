"""Pydantic-схемы для получателей и их конфигов."""
from datetime import datetime

from pydantic import BaseModel

from app.db.models import RecipientStatus


class ConfigRead(BaseModel):
    """Ответ: конфиг получателя."""

    id: int
    name: str

    model_config = {"from_attributes": True}


class RecipientCreate(BaseModel):
    """Тело запроса на добавление одного получателя."""

    email: str
    name: str | None = None
    configs: list[str] = []


class RecipientsBulk(BaseModel):
    """Массовое добавление получателей."""

    items: list[RecipientCreate]


class RecipientRead(BaseModel):
    """Ответ: получатель со статусом отправки и списком конфигов."""

    id: int
    campaign_id: int
    email: str
    name: str | None = None
    status: RecipientStatus
    error: str | None = None
    sent_at: datetime | None = None
    configs: list[ConfigRead] = []

    model_config = {"from_attributes": True}
