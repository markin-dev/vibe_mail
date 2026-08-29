"""Фоновый поток генерации конфигов.

Запускается вместе с приложением (через lifespan) и обрабатывает конфиги в статусе
QUEUED: берёт по одному, получает файл у источника (`config_generator`) и складывает его
в БД. Источник правды — статусы в БД, поэтому процесс возобновляем: при старте «зависшие»
GENERATING возвращаются в очередь.
"""

import logging
import threading
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import Config, ConfigStatus
from app.db.session import SessionLocal
from app.services.config_generator import ConfigSource

log = logging.getLogger("vibe_mail.config_worker")

# Пауза между опросами очереди, секунды.
IDLE_INTERVAL = 1.0


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

    # ------------------------------------------------------------------ #
    # Цикл
    # ------------------------------------------------------------------ #

    def _loop(self) -> None:
        log.info("Воркер генерации конфигов запущен")
        while not self._stop.is_set():
            self._tick()
            self._stop.wait(IDLE_INTERVAL)
        log.info("Воркер генерации конфигов остановлен")

    def _tick(self) -> None:
        """Один проход по очереди конфигов."""
        try:
            with SessionLocal() as db:
                self._process_queued(db)
        except Exception:  # воркер не должен падать по одной ошибке
            log.exception("Ошибка в цикле воркера конфигов, повтор через секунду")

    def _process_queued(self, db: Session) -> None:
        for config in self._queued_configs(db):
            if self._stop.is_set():
                return
            self._process(db, config)

    def _process(self, db: Session, config: Config) -> None:
        """Один конфиг: QUEUED → GENERATING → READY либо FAILED."""
        self._mark_generating(db, config)

        try:
            filename, content = self.source.generate(config.name)
        except Exception as exc:  # noqa: BLE001 - ошибка одного конфига не рушит очередь
            self._mark_failed(db, config, exc)
            return

        self._store_result(db, config, filename, content)

    # ------------------------------------------------------------------ #
    # Переходы статусов
    # ------------------------------------------------------------------ #

    @staticmethod
    def _mark_generating(db: Session, config: Config) -> None:
        config.status = ConfigStatus.GENERATING
        db.commit()

    @staticmethod
    def _mark_failed(db: Session, config: Config, exc: Exception) -> None:
        config.status = ConfigStatus.FAILED
        config.error = str(exc)
        db.commit()
        log.error("Не удалось получить конфиг %s", config.name, exc_info=exc)

    @staticmethod
    def _store_result(db: Session, config: Config, filename: str, content: bytes) -> None:
        config.filename = filename
        config.content = content
        config.size = len(content)
        config.status = ConfigStatus.READY
        config.error = None
        config.generated_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()

    # ------------------------------------------------------------------ #
    # Запросы
    # ------------------------------------------------------------------ #

    @staticmethod
    def _queued_configs(db: Session) -> list[Config]:
        return db.query(Config).filter_by(status=ConfigStatus.QUEUED).order_by(Config.id).all()
