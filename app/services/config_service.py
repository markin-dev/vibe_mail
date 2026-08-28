"""Работа с конфигами получателей: постановка в очередь на генерацию, доступ к файлу."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.models import Config, ConfigStatus, Recipient


def enqueue_campaign_configs(db: Session, campaign_id: int) -> int:
    """Ставит в очередь конфиги кампании, у которых ещё нет файла.

    Готовые (READY) не трогаем — повторное нажатие кнопки догенерирует только
    недостающие и перезапустит упавшие. Возвращает количество поставленных в очередь.
    """
    configs = (
        db.query(Config)
        .join(Recipient, Config.recipient_id == Recipient.id)
        .filter(
            Recipient.campaign_id == campaign_id,
            Config.status.in_([ConfigStatus.PENDING, ConfigStatus.FAILED]),
        )
        .all()
    )

    for config in configs:
        config.status = ConfigStatus.QUEUED
        config.error = None

    db.commit()
    return len(configs)


def get_config(db: Session, config_id: int) -> Config:
    config = db.get(Config, config_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Конфиг не найден")
    return config
