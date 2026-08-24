"""Pydantic-схемы для получателей и вложений."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.db.models import RecipientStatus


class RecipientCreate(BaseModel):
    """Тело запроса на добавление одного получателя."""

    email: str
    name: Optional[str] = None


class RecipientsBulk(BaseModel):
    """Массовое добавление получателей."""

    items: list[RecipientCreate]


class AttachmentRead(BaseModel):
    """Ответ: метаданные вложения."""

    id: int
    filename: str
    size: int

    model_config = {"from_attributes": True}


class RecipientRead(BaseModel):
    """Ответ: получатель со статусом и списком вложений."""

    id: int
    campaign_id: int
    email: str
    name: Optional[str] = None
    status: RecipientStatus
    error: Optional[str] = None
    sent_at: Optional[datetime] = None
    attachments: list[AttachmentRead] = []

    model_config = {"from_attributes": True}
