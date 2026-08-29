"""ORM-модели: Campaign, Recipient, Config."""

import datetime
import enum

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _now() -> datetime.datetime:
    """Текущее время в UTC (naive) — для полей created_at/sent_at."""
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


class CampaignStatus(enum.StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DONE_WITH_ERRORS = "done_with_errors"
    ERROR = "error"


class RecipientStatus(enum.StrEnum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ConfigStatus(enum.StrEnum):
    PENDING = "pending"  # имя есть, файла ещё нет
    QUEUED = "queued"  # поставлен в очередь на генерацию
    GENERATING = "generating"  # воркер взял в работу
    READY = "ready"
    FAILED = "failed"


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(1024))
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus), default=CampaignStatus.NEW
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=_now)

    recipients: Mapped[list["Recipient"]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class Recipient(Base):
    __tablename__ = "recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(320), index=True)
    name: Mapped[str | None] = mapped_column(String(320), nullable=True)
    status: Mapped[RecipientStatus] = mapped_column(
        SAEnum(RecipientStatus), default=RecipientStatus.PENDING
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="recipients")
    configs: Mapped[list["Config"]] = relationship(
        back_populates="recipient", cascade="all, delete-orphan", order_by="Config.id"
    )


class Config(Base):
    """Конфиг, который уезжает получателю: имя плюс сам файл.

    Файл хранится здесь же (`content` — BLOB): конфиги весят единицы килобайт, поэтому
    отдельной сущности под файл не заводим. Пока имя не сгенерировано, `content` пуст,
    а статус показывает, на какой стадии конфиг.
    """

    __tablename__ = "configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_id: Mapped[int] = mapped_column(
        ForeignKey("recipients.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[ConfigStatus] = mapped_column(SAEnum(ConfigStatus), default=ConfigStatus.PENDING)
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    content: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    recipient: Mapped["Recipient"] = relationship(back_populates="configs")

    @property
    def download_filename(self) -> str:
        """Имя файла для отдачи наружу: сгенерированное либо собранное из имени конфига."""
        return self.filename or f"{self.name}.conf"
