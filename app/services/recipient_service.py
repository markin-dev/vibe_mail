"""Работа с получателями: валидация, добавление, готовность к отправке."""
from email.utils import parseaddr

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.constants import EMAIL_RE
from app.db.models import Campaign, Config, Recipient, RecipientStatus
from app.schemas.recipient import RecipientCreate


def validate_email(email: str) -> bool:
    """Проверка синтаксиса email."""
    return bool(EMAIL_RE.match(parseaddr(email)[1] or email))


def add_recipients(db: Session, campaign_id: int, items: list[RecipientCreate]) -> list[Recipient]:
    """Добавляет получателей с валидацией.

    Почта приводится к нижнему регистру — в таком виде и сохраняется, как при импорте
    вставленного списка (`import_service`).

    Атомарно: при любой ошибке (некорректный синтаксис, дубликат в кампании или в
    пакете) ничего не создаётся, возвращается HTTPException 400 со списком проблем.
    """
    existing = {
        row[0].lower()
        for row in db.query(Recipient.email).filter_by(campaign_id=campaign_id).all()
    }
    seen = set(existing)
    problems: list[str] = []
    to_create: list[Recipient] = []

    for idx, item in enumerate(items, start=1):
        email = item.email.strip().lower()
        if not email or not validate_email(email):
            problems.append(f"recipients[{idx}]: некорректный адрес {email!r}")
            continue
        if email in seen:
            problems.append(f"recipients[{idx}]: дубликат адреса {email}")
            continue
        seen.add(email)
        recipient = Recipient(
            campaign_id=campaign_id,
            email=email,
            name=item.name,
            status=RecipientStatus.PENDING,
        )
        recipient.configs = [Config(name=name) for name in item.configs]
        to_create.append(recipient)

    if problems:
        raise HTTPException(status_code=400, detail={"errors": problems})

    db.add_all(to_create)
    db.commit()
    for r in to_create:
        db.refresh(r)
    return to_create


def get_recipients(
    db: Session, campaign_id: int, status: RecipientStatus | None = None
) -> list[Recipient]:
    query = db.query(Recipient).filter_by(campaign_id=campaign_id)
    if status is not None:
        query = query.filter_by(status=status)
    return query.order_by(Recipient.id).all()


def get_recipient(db: Session, recipient_id: int) -> Recipient:
    recipient = db.get(Recipient, recipient_id)
    if recipient is None:
        raise HTTPException(status_code=404, detail="Получатель не найден")
    return recipient


def validate_campaign_ready(db: Session, campaign: Campaign) -> list[str]:
    """Проверяет, готова ли кампания к отправке.

    Возвращает список проблем; пустой список = можно отправлять.
    """
    problems: list[str] = []
    recipients = db.query(Recipient).filter_by(campaign_id=campaign.id).all()

    if not recipients:
        problems.append("В кампании нет получателей")

    problems.extend(
        f"{r.email}: не указано ни одного конфига" for r in recipients if not r.configs
    )

    return problems
