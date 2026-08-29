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
_INVISIBLE = str.maketrans({"\u00a0": " ", "\u200b": "", "\ufeff": ""})

_EXPECTED_COLUMNS = 2


@dataclass
class ParsedGroup:
    """Получатель и его конфиги в порядке появления во вставке.

    Почта уже приведена к нижнему регистру — в таком виде она и уходит в БД.
    """

    email: str
    configs: list[str] = field(default_factory=list)


@dataclass
class ParsedRow:
    """Успешно разобранная строка вставки."""

    config_name: str
    email: str


@dataclass
class _GroupOutcome:
    """Что случилось с одной группой при импорте — для подсчёта итогов."""

    is_created: bool
    is_updated: bool
    created_configs: int


# ---------------------------------------------------------------------- #
# Разбор текста
# ---------------------------------------------------------------------- #


def _normalize_text(text: str) -> str:
    """Приводит переводы строк к \\n и вычищает невидимые символы из таблиц."""
    return text.replace("\r\n", "\n").replace("\r", "\n").translate(_INVISIBLE)


def _parse_line(lineno: int, raw_line: str) -> ParsedRow | ImportRowProblem | None:
    """Разбирает одну строку вставки.

    `None` — пустая строка (пропускаем молча), `ImportRowProblem` — строку принять нельзя,
    иначе `ParsedRow` с именем конфига и почтой в нижнем регистре.
    """
    if not raw_line.strip():
        return None

    raw = raw_line.strip()
    cells = [cell.strip() for cell in raw_line.split("\t")]

    if len(cells) != _EXPECTED_COLUMNS:
        return ImportRowProblem(
            line=lineno,
            raw=raw,
            reason="ожидались две колонки через таб: имя конфига и почта",
        )

    config_name, email = cells[0], cells[1].lower()

    if not config_name:
        return ImportRowProblem(line=lineno, raw=raw, reason="не указано имя конфига")
    if not email:
        return ImportRowProblem(line=lineno, raw=raw, reason="не указана почта")
    if not validate_email(email):
        return ImportRowProblem(line=lineno, raw=raw, reason=f"некорректная почта {email}")

    return ParsedRow(config_name=config_name, email=email)


def parse_recipients_text(text: str) -> tuple[list[ParsedGroup], list[ImportRowProblem]]:
    """Разбирает вставленный текст в группы «почта → конфиги» и список проблем.

    Почта приводится к нижнему регистру, поэтому строки, отличающиеся только регистром
    адреса, попадают в одну группу (и в одно письмо).

    Проблемная строка не импортируется, но и не блокирует остальные: возвращается
    отдельным списком с номером строки, исходным текстом и причиной.
    """
    grouped: dict[str, ParsedGroup] = {}
    problems: list[ImportRowProblem] = []

    for lineno, raw_line in enumerate(_normalize_text(text).split("\n"), start=1):
        row = _parse_line(lineno, raw_line)

        if row is None:
            continue
        if isinstance(row, ImportRowProblem):
            problems.append(row)
            continue

        group = grouped.setdefault(row.email, ParsedGroup(email=row.email))
        group.configs.append(row.config_name)

    return list(grouped.values()), problems


# ---------------------------------------------------------------------- #
# Предпросмотр и импорт
# ---------------------------------------------------------------------- #


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


def _build_preview_group(group: ParsedGroup, recipient: Recipient | None) -> ImportGroup:
    """Одна строка предпросмотра: что реально добавится этому получателю."""
    existing_configs = [c.name for c in recipient.configs] if recipient else []

    return ImportGroup(
        email=group.email,
        configs=_new_config_names(group.configs, existing_configs),
        existing_configs=existing_configs,
        is_existing=recipient is not None,
    )


def build_preview(db: Session, campaign_id: int, text: str) -> ImportPreview:
    """Показывает, что получится при импорте. Ничего не пишет в БД.

    В `configs` попадают только те конфиги, которые реально добавятся: имена, уже
    заведённые у получателя, показываются отдельно в `existing_configs`.
    """
    groups, problems = parse_recipients_text(text)
    existing = _get_existing_recipients(db, campaign_id)

    preview_groups = [_build_preview_group(group, existing.get(group.email)) for group in groups]

    return ImportPreview(
        groups=preview_groups,
        problems=problems,
        total_rows=sum(len(g.configs) for g in groups) + len(problems),
        total_configs=sum(len(g.configs) for g in preview_groups),
    )


def _apply_group(
    db: Session, campaign_id: int, group: ParsedGroup, existing: dict[str, Recipient]
) -> _GroupOutcome:
    """Заводит получателя (если нужно) и дописывает ему недостающие конфиги."""
    recipient = existing.get(group.email)
    is_created = recipient is None

    if recipient is None:
        recipient = Recipient(
            campaign_id=campaign_id,
            email=group.email,
            status=RecipientStatus.PENDING,
        )
        db.add(recipient)

    new_names = _new_config_names(group.configs, [c.name for c in recipient.configs])
    recipient.configs.extend(Config(name=name) for name in new_names)

    return _GroupOutcome(
        is_created=is_created,
        # id есть только у уже существовавшего получателя (autoflush выключен).
        is_updated=bool(new_names) and recipient.id is not None,
        created_configs=len(new_names),
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

    outcomes = [_apply_group(db, campaign_id, group, existing) for group in groups]
    db.commit()

    return ImportResult(
        created_recipients=sum(o.is_created for o in outcomes),
        updated_recipients=sum(o.is_updated for o in outcomes),
        created_configs=sum(o.created_configs for o in outcomes),
        problems=problems,
    )
