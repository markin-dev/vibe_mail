"""Фоновый поток генерации конфигов.

Запускается вместе с приложением (через lifespan) и обрабатывает конфиги в статусе
QUEUED: берёт по одному, получает файл у источника (`config_generator`) и складывает его
в БД. Источник правды — статусы в БД, поэтому процесс возобновляем: при старте «зависшие»
GENERATING возвращаются в очередь.
"""
import logging
import threading
import time
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import Config, ConfigStatus
from app.db.session import SessionLocal
from app.services.config_generator import ConfigSource

log = logging.getLogger("vibe_mail.config_worker")


class ConfigWorker:
    """Потоковый воркер генерации конфигов."""

    def __init__(self, source: ConfigSource) -> None:
        self.source = source
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._requeue_stuck()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=30)
        self.source.close()

    @staticmethod
    def _requeue_stuck() -> None:
        """Возвращает в очередь конфиги, на которых процесс прервался."""
        with SessionLocal() as db:
            stuck = db.query(Config).filter_by(status=ConfigStatus.GENERATING).all()
            for config in stuck:
                config.status = ConfigStatus.QUEUED
            if stuck:
                db.commit()
                log.info("Возвращено в очередь конфигов: %d", len(stuck))

    def _loop(self) -> None:
        log.info("Воркер генерации конфигов запущен")
        while not self._stop.is_set():
            try:
                with SessionLocal() as db:
                    queued = (
                        db.query(Config)
                        .filter_by(status=ConfigStatus.QUEUED)
                        .order_by(Config.id)
                        .all()
                    )
                    for config in queued:
                        if self._stop.is_set():
                            break
                        self._process(db, config)
            except Exception:  # noqa: BLE001 - воркер не должен падать по одной ошибке
                log.exception("Ошибка в цикле воркера конфигов, повтор через секунду")

            if not self._stop.is_set():
                time.sleep(1)
        log.info("Воркер генерации конфигов остановлен")

    def _process(self, db: Session, config: Config) -> None:
        config.status = ConfigStatus.GENERATING
        db.commit()

        try:
            filename, content = self.source.generate(config.name)
        except Exception as exc:  # noqa: BLE001 - ошибка одного конфига не рушит очередь
            config.status = ConfigStatus.FAILED
            config.error = str(exc)
            db.commit()
            log.error("Не удалось получить конфиг %s: %s", config.name, exc)
            return

        config.filename = filename
        config.content = content
        config.size = len(content)
        config.status = ConfigStatus.READY
        config.error = None
        config.generated_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
