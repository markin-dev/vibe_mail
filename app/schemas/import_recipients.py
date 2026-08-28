"""Pydantic-схемы импорта получателей из вставленного списка."""
from pydantic import BaseModel


class RecipientsImportText(BaseModel):
    """Тело запроса: вставленный из таблицы текст (две колонки через таб)."""

    text: str


class ImportRowProblem(BaseModel):
    """Строка, которую не удалось разобрать."""

    line: int
    raw: str
    reason: str


class ImportGroup(BaseModel):
    """Одно письмо: получатель и конфиги, которые ему уедут."""

    email: str
    configs: list[str]
    existing_configs: list[str] = []
    is_existing: bool = False


class ImportPreview(BaseModel):
    """Предпросмотр импорта: что получится, если сохранить."""

    groups: list[ImportGroup]
    problems: list[ImportRowProblem] = []
    total_rows: int
    total_configs: int


class ImportResult(BaseModel):
    """Итог импорта."""

    created_recipients: int
    updated_recipients: int
    created_configs: int
    problems: list[ImportRowProblem] = []
