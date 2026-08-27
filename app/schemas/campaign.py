"""Pydantic-схемы для кампаний (входные и выходные данные API)."""
from datetime import datetime

from pydantic import BaseModel

from app.db.models import CampaignStatus


class CampaignCreate(BaseModel):
    """Тело запроса на создание кампании."""

    name: str
    subject: str
    body: str
    body_html: str | None = None
    from_name: str | None = None


class CampaignRead(BaseModel):
    """Ответ: данные кампании + необязательные счётчики прогресса."""

    id: int
    name: str
    subject: str
    body: str
    body_html: str | None = None
    from_name: str | None = None
    status: CampaignStatus
    created_at: datetime
    totals: dict | None = None

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    """Универсальный ответ операции (старт/стоп/импорт)."""

    detail: str
    campaign_id: int


class ImportCsvResult(BaseModel):
    """Результат импорта получателей из CSV."""

    created: int
    skipped: list[tuple[int, str, str]] = []
    problems: list[str] = []
