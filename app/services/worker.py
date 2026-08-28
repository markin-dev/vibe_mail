"""Фоновый поток отправки писем.

Запускается вместе с приложением (через lifespan) и последовательно обрабатывает
кампании со статусом IN_PROGRESS: берёт pending-получателей, отправляет через
MailSender, обновляет статусы в БД. БД — источник правды, поэтому при старте
процесса «зависшие» in_progress-кампании подхватываются автоматически (возобновление).
"""
import logging
import threading
import time
from datetime import UTC, datetime

from app.core.config import Settings
from app.db.models import Campaign, CampaignStatus, Recipient, RecipientStatus
from app.db.session import SessionLocal
from app.services.mail_sender import MailSender

log = logging.getLogger("vibe_mail.worker")


class Worker:
    """Потоковый воркер отправки писем."""

    def __init__(self, settings: Settings, mail_sender: MailSender) -> None:
        self.settings = settings
        self.mail_sender = mail_sender
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=30)

    def _loop(self) -> None:
        log.info("Воркер отправки запущен")
        while not self._stop.is_set():
            try:
                with SessionLocal() as db:
                    running = db.query(Campaign).filter_by(status=CampaignStatus.IN_PROGRESS).all()
                    for camp in running:
                        pending = (
                            db.query(Recipient)
                            .filter_by(campaign_id=camp.id, status=RecipientStatus.PENDING)
                            .order_by(Recipient.id)
                            .all()
                        )
                        if not pending:
                            has_failed = (
                                db.query(Recipient)
                                .filter_by(campaign_id=camp.id, status=RecipientStatus.FAILED)
                                .first()
                                is not None
                            )
                            camp.status = (
                                CampaignStatus.DONE_WITH_ERRORS
                                if has_failed
                                else CampaignStatus.DONE
                            )
                            db.commit()
                            log.info(
                                "Кампания %s завершена (%s)",
                                camp.id,
                                "есть ошибки отправки" if has_failed else "все письма обработаны",
                            )
                            continue

                        for r in pending:
                            if self._stop.is_set():
                                break
                            configs = [c.name for c in r.configs]
                            ok, err = self.mail_sender.send(camp, r, configs)
                            r.status = RecipientStatus.SENT if ok else RecipientStatus.FAILED
                            r.error = err
                            r.sent_at = (
                                datetime.now(UTC).replace(tzinfo=None) if ok else None
                            )
                            db.commit()
                            if ok:
                                log.info("[%s] Отправлено: %s", camp.id, r.email)
                            else:
                                log.error("[%s] Ошибка для %s: %s", camp.id, r.email, err)
                            if not self._stop.is_set():
                                time.sleep(self.settings.DEFAULT_DELAY)
            except Exception:  # noqa: BLE001 - воркер не должен падать по одной ошибке
                log.exception("Ошибка в цикле воркера, повтор через секунду")

            if not self._stop.is_set():
                time.sleep(1)
        log.info("Воркер отправки остановлен")
