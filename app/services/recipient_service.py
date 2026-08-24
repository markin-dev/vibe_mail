"""Работа с получателями: валидация, добавление, вложения, готовность к отправке."""
import os
from email.utils import parseaddr
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import EMAIL_RE
from app.db.models import Attachment, Campaign, Recipient, RecipientStatus
from app.schemas.recipient import RecipientCreate


def _safe_filename(name: str) -> str:
    """Оставляем только имя файла без путей (защита от path traversal)."""
    return Path(name).name


def human(num: float) -> str:
    """Человекочитаемый размер (Б/КБ/МБ/ГБ)."""
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if num < 1024 or unit == "ГБ":
            return f"{num:.0f} {unit}" if unit == "Б" else f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.0f} Б"


def validate_email(email: str) -> bool:
    """Проверка синтаксиса email (как в оригинальном send_mail.validate)."""
    return bool(EMAIL_RE.match(parseaddr(email)[1] or email))


def add_recipients(db: Session, campaign_id: int, items: list[RecipientCreate]) -> list[Recipient]:
    """Добавляет получателей с валидацией.

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
        email = item.email.strip()
        if not email or not validate_email(email):
            problems.append(f"recipients[{idx}]: некорректный адрес {email!r}")
            continue
        key = email.lower()
        if key in seen:
            problems.append(f"recipients[{idx}]: дубликат адреса {email}")
            continue
        seen.add(key)
        to_create.append(
            Recipient(
                campaign_id=campaign_id,
                email=email,
                name=item.name,
                status=RecipientStatus.PENDING,
            )
        )

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


def add_attachment(db: Session, recipient: Recipient, filename: str, content: bytes) -> Attachment:
    """Сохраняет файл вложения и создаёт запись Attachment.

    Путь: ATTACHMENTS_DIR/{campaign_id}/{имя_файла}. При совпадении имени добавляем
    суффикс, чтобы не перезатирать чужие файлы.
    """
    settings = get_settings()
    dest_dir = settings.ATTACHMENTS_DIR.resolve() / str(recipient.campaign_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    safe = _safe_filename(filename)
    dest = dest_dir / safe
    counter = 1
    while dest.exists():
        stem, suffix = Path(safe).stem, Path(safe).suffix
        dest = dest_dir / f"{stem}_{counter}{suffix}"
        counter += 1

    dest.write_bytes(content)
    attachment = Attachment(
        recipient_id=recipient.id, filename=safe, stored_path=str(dest), size=len(content)
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def validate_campaign_ready(db: Session, campaign: Campaign) -> list[str]:
    """Проверяет, готова ли кампания к отправке (файлы есть, лимит не превышен).

    Возвращает список проблем; пустой список = можно отправлять. Заменяет
    validate() из оригинального send_mail.py.
    """
    settings = get_settings()
    problems: list[str] = []
    recipients = db.query(Recipient).filter_by(campaign_id=campaign.id).all()

    for r in recipients:
        total = 0
        for att in r.attachments:
            path = Path(att.stored_path)
            if not path.is_file():
                problems.append(f"{r.email}: файл не найден — {att.filename}")
                continue
            if not os.access(path, os.R_OK):
                problems.append(f"{r.email}: нет прав на чтение — {att.filename}")
                continue
            total += att.size
        if total * settings.BASE64_OVERHEAD > settings.MAX_ATTACHMENT_BYTES:
            problems.append(
                f"{r.email}: вложения весят {human(total)} "
                f"(~{human(int(total * settings.BASE64_OVERHEAD))} после кодирования), "
                f"лимит {human(settings.MAX_ATTACHMENT_BYTES)}"
            )
    return problems
