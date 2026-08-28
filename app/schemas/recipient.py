"""Pydantic-схемы для получателей и вложений."""
from datetime import datetime

from pydantic import BaseModel

from app.db.models import RecipientStatus


class RecipientCreate(BaseModel):
    """Тело запроса на добавление одного получателя."""

    email: str
    name: str | None = None


class RecipientsBulk(BaseModel):
    """Массовое добавление получателей."""

    items: list[RecipientCreate]


class RecipientRead(BaseModel):
    """Ответ: получатель со статусом отправки."""

    id: int
    campaign_id: int
    email: str
    name: str | None = None
    status: RecipientStatus
    error: str | None = None
    sent_at: datetime | None = None

    model_config = {"from_attributes": True}
