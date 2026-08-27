"""Универсальная обёртка ответов API.

Все JSON-эндпоинты данных возвращают единый формат:
    {"status": "success" | "error", "result": <данные>, "error": <сообщение>}

Ошибки (HTTPException, ошибки валидации, необработанные исключения)
перехватываются в `app/main.py` и тоже оборачиваются в этот формат.

Для каждого конкретного ответа заведён отдельный подкласс (например,
`CampaignReadEnvelope`), чтобы в сгенерированной OpenAPI-схеме были
стабильные, читаемые имена (generic даёт хешированные суффиксы).
"""
from typing import Literal

from pydantic import BaseModel

from app.schemas.campaign import (
    CampaignRead,
    ImportCsvResult,
    MessageOut,
)
from app.schemas.recipient import AttachmentRead, RecipientRead


class ApiEnvelope[T](BaseModel):
    """Базовая обёртка ответа."""

    status: Literal["success", "error"] = "success"
    result: T | None = None
    error: str | None = None


def ok[T](result: T | None = None) -> ApiEnvelope[T]:
    """Успешный ответ-обёртка."""
    return ApiEnvelope[T](status="success", result=result, error=None)


class CampaignReadEnvelope(ApiEnvelope[CampaignRead]):
    """Обёртка одной кампании."""


class ListCampaignReadEnvelope(ApiEnvelope[list[CampaignRead]]):
    """Обёртка списка кампаний."""


class RecipientReadEnvelope(ApiEnvelope[RecipientRead]):
    """Обёртка одного получателя."""


class ListRecipientReadEnvelope(ApiEnvelope[list[RecipientRead]]):
    """Обёртка списка получателей."""


class AttachmentReadEnvelope(ApiEnvelope[AttachmentRead]):
    """Обёртка вложения."""


class MessageOutEnvelope(ApiEnvelope[MessageOut]):
    """Обёртка служебного сообщения (старт/стоп)."""


class ImportCsvResultEnvelope(ApiEnvelope[ImportCsvResult]):
    """Обёртка результата импорта CSV."""
