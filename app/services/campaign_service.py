"""Работа с кампаниями: CRUD, прогресс, импорт получателей из CSV."""
import csv
import io

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import EMAIL_RE
from app.db.models import (
    Attachment,
    Campaign,
    CampaignStatus,
    Recipient,
    RecipientStatus,
)
from app.schemas.campaign import CreateCampaign
from app.services.recipient_service import _safe_filename


def create_campaign(db: Session, data: CreateCampaign) -> Campaign:
    campaign = Campaign(
        name=data.name,
        subject=data.subject,
        body=data.body,
        status=CampaignStatus.NEW,
    )
    db.add(campaign)
    db.commit()
    return campaign


def list_campaigns(db: Session) -> list[Campaign]:
    return db.query(Campaign).order_by(Campaign.id.desc()).all()


def get_campaign(db: Session, campaign_id: int) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    return campaign


def get_progress(db: Session, campaign: Campaign) -> dict:
    rows = (
        db.query(Recipient.status, func.count(Recipient.id))
        .filter_by(campaign_id=campaign.id)
        .group_by(Recipient.status)
        .all()
    )
    counts = {status.value: n for status, n in rows}
    return {
        "sent": counts.get("sent", 0),
        "failed": counts.get("failed", 0),
        "pending": counts.get("pending", 0),
        "skipped": counts.get("skipped", 0),
        "total": sum(counts.values()),
    }


def set_status(db: Session, campaign: Campaign, status: CampaignStatus) -> Campaign:
    campaign.status = status
    db.commit()
    return campaign


def import_csv(
    db: Session, campaign_id: int, content: bytes, encoding: str = "utf-8-sig"
) -> dict:
    """Импорт получателей из CSV (имя,email,файл).

    Строки с одинаковым email объединяются в одного получателя со всеми файлами.
    Строки без email пропускаются и возвращаются отдельным списком. Файлы пока не
    загружаются — создаются записи Attachment с ожидаемым путём (size=0); реальную
    загрузку делает endpoint вложений. Перенос логики из import_csv.py.
    """
    text = content.decode(encoding, errors="replace")
    reader = csv.reader(io.StringIO(text))

    grouped: dict[str, dict] = {}
    skipped: list[tuple[int, str, str]] = []
    problems: list[str] = []

    for lineno, row in enumerate(reader, start=1):
        row = [c.strip() for c in row]
        if not any(row):
            continue
        if len(row) < 3:
            problems.append(f"строка {lineno}: ожидалось 3 колонки, получено {len(row)}: {row}")
            continue
        name, email, filename = row[0], row[1], row[2]
        if not filename:
            problems.append(f"строка {lineno}: не указан файл вложения")
            continue
        if not email:
            skipped.append((lineno, name, filename))
            continue
        if not EMAIL_RE.match(email):
            problems.append(f"строка {lineno}: некорректный адрес {email!r}")
            continue
        entry = grouped.setdefault(email.lower(), {"email": email, "name": name, "files": []})
        if filename in entry["files"]:
            problems.append(f"строка {lineno}: файл {filename} уже добавлен для {email}")
            continue
        entry["files"].append(filename)

    base = get_settings().ATTACHMENTS_DIR.resolve()
    recipients: list[Recipient] = []
    for entry in grouped.values():
        recipient = Recipient(
            campaign_id=campaign_id,
            email=entry["email"],
            name=entry["name"] or None,
            status=RecipientStatus.PENDING,
        )
        for fname in entry["files"]:
            expected = base / str(campaign_id) / _safe_filename(fname)
            recipient.attachments.append(
                Attachment(filename=fname, stored_path=str(expected), size=0)
            )
        recipients.append(recipient)

    db.add_all(recipients)
    db.commit()

    return {"created": len(recipients), "skipped": skipped, "problems": problems}
