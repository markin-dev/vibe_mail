"""Разбор вставленного из таблицы списка получателей.

Единственное место, где живёт парсинг: и предпросмотр, и импорт ходят сюда.

Формат жёсткий — ровно две колонки, разделённые табом: имя конфига и почта.
Именно это Google Sheets кладёт в буфер при копировании диапазона ячеек. Строки
с одинаковой почтой объединяются в одно письмо с несколькими конфигами.
"""
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.db.models import Config, Recipient, RecipientStatus
from app.schemas.import_recipients import (
    ImportGroup,
    ImportPreview,
    ImportResult,
    ImportRowProblem,
)
from app.services.recipient_service import validate_email

# Невидимые символы, которые приезжают вместе со вставкой из таблиц и ломают
# проверку адреса: неразрывный пробел, zero-width space, BOM.
_INVISIBLE = str.maketrans({" ": " ", "​": "", "﻿": ""})

_EXPECTED_COLUMNS = 2


@dataclass
class ParsedGroup:
    """Получатель и его конфиги в порядке появления во вставке."""

    email: str
    configs: list[str] = field(default_factory=list)


def parse_recipients_text(text: str) -> tuple[list[ParsedGroup], list[ImportRowProblem]]:
    """Разбирает вставленный текст в группы «почта → конфиги» и список проблем.

    Проблемная строка не импортируется, но и не блокирует остальные: возвращается
    отдельным списком с номером строки, исходным текстом и причиной.
    """
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").translate(_INVISIBLE)

    grouped: dict[str, ParsedGroup] = {}
    problems: list[ImportRowProblem] = []

    for lineno, raw_line in enumerate(normalized.split("\n"), start=1):
        if not raw_line.strip():
            continue

        cells = [cell.strip() for cell in raw_line.split("\t")]
        raw = raw_line.strip()

        if len(cells) != _EXPECTED_COLUMNS:
            problems.append(
                ImportRowProblem(
                    line=lineno,
                    raw=raw,
                    reason="ожидались две колонки через таб: имя конфига и почта",
                )
            )
            continue

        config_name, email = cells
        if not config_name:
            problems.append(
                ImportRowProblem(line=lineno, raw=raw, reason="не указано имя конфига")
            )
            continue
        if not email:
            problems.append(ImportRowProblem(line=lineno, raw=raw, reason="не указана почта"))
            continue
        if not validate_email(email):
            problems.append(
                ImportRowProblem(line=lineno, raw=raw, reason=f"некорректная почта {email}")
            )
            continue

        group = grouped.setdefault(email.lower(), ParsedGroup(email=email))
        group.configs.append(config_name)

    return list(grouped.values()), problems


def _get_existing_recipients(db: Session, campaign_id: int) -> dict[str, Recipient]:
    """Получатели кампании по нормализованной почте."""
    recipients = db.query(Recipient).filter_by(campaign_id=campaign_id).all()
    return {r.email.lower(): r for r in recipients}


def _new_config_names(names: list[str], known_names: list[str]) -> list[str]:
    """Имена, которых у получателя ещё нет — в порядке появления, без повторов."""
    known = set(known_names)
    result: list[str] = []

    for name in names:
        if name not in known:
            known.add(name)
            result.append(name)

    return result


def build_preview(db: Session, campaign_id: int, text: str) -> ImportPreview:
    """Показывает, что получится при импорте. Ничего не пишет в БД.

    В `configs` попадают только те конфиги, которые реально добавятся: имена, уже
    заведённые у получателя, показываются отдельно в `existing_configs`.
    """
    groups, problems = parse_recipients_text(text)
    existing = _get_existing_recipients(db, campaign_id)

    preview_groups = []
    for group in groups:
        recipient = existing.get(group.email.lower())
        existing_configs = [c.name for c in recipient.configs] if recipient else []

        preview_groups.append(
            ImportGroup(
                email=group.email,
                configs=_new_config_names(group.configs, existing_configs),
                existing_configs=existing_configs,
                is_existing=recipient is not None,
            )
        )

    return ImportPreview(
        groups=preview_groups,
        problems=problems,
        total_rows=sum(len(g.configs) for g in groups) + len(problems),
        total_configs=sum(len(g.configs) for g in preview_groups),
    )


def import_recipients(db: Session, campaign_id: int, text: str) -> ImportResult:
    """Импортирует разобранные строки в кампанию.

    Импорт частичный: валидные строки сохраняются, проблемные возвращаются списком.
    Если почта уже есть в кампании, конфиги дописываются существующему получателю.
    Повторное имя конфига у одного получателя не задваивается — так повторный импорт
    того же списка остаётся безопасным.
    """
    groups, problems = parse_recipients_text(text)
    existing = _get_existing_recipients(db, campaign_id)

    created_recipients = 0
    updated_recipients = 0
    created_configs = 0

    for group in groups:
        recipient = existing.get(group.email.lower())

        if recipient is None:
            recipient = Recipient(
                campaign_id=campaign_id,
                email=group.email,
                status=RecipientStatus.PENDING,
            )
            db.add(recipient)
            created_recipients += 1

        new_names = _new_config_names(group.configs, [c.name for c in recipient.configs])
        recipient.configs.extend(Config(name=name) for name in new_names)
        created_configs += len(new_names)

        if new_names and recipient.id is not None:
            updated_recipients += 1

    db.commit()

    return ImportResult(
        created_recipients=created_recipients,
        updated_recipients=updated_recipients,
        created_configs=created_configs,
        problems=problems,
    )
