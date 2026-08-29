"""Отправка писем через SMTP.

Инкапсулирует всю работу с smtplib: подключение (SSL/STARTTLS), сборку
письма, ретраи с переподключением. Не ходит в базу — получает готовые объекты
кампании, получателя и его конфигов с уже загруженным содержимым файлов.
"""

from __future__ import annotations

import contextlib
import logging
import mimetypes
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import formataddr
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.config import Settings
    from app.db.models import Campaign, Config, Recipient

log = logging.getLogger("vibe_mail.mail_sender")


class MailSender:
    """Класс-интерфейс отправки писем одному получателю."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    # ------------------------------------------------------------------ #
    # Внутреннее: подключение и сборка письма
    # ------------------------------------------------------------------ #

    def _connect(self) -> smtplib.SMTP | smtplib.SMTP_SSL:
        """Устанавливает соединение с SMTP и логинится."""
        host = self.settings.SMTP_HOST
        port = int(self.settings.SMTP_PORT)
        context = ssl.create_default_context()
        use_ssl = self.settings.SMTP_USE_SSL or port == 465

        if use_ssl:
            smtp = smtplib.SMTP_SSL(host, port, context=context, timeout=30)
        else:
            smtp = smtplib.SMTP(host, port, timeout=30)
            smtp.ehlo()
            if self.settings.SMTP_USE_TLS:
                smtp.starttls(context=context)
                smtp.ehlo()

        smtp.login(self.settings.SMTP_USER, self.settings.SMTP_PASSWORD)
        log.info("Подключено к %s:%s как %s", host, port, self.settings.SMTP_USER)
        return smtp

    @staticmethod
    def _format_to(recipient: Recipient) -> str:
        """Заголовок To: с именем, если оно есть, иначе голый адрес."""
        if not recipient.name:
            return recipient.email
        return formataddr((recipient.name, recipient.email))

    @staticmethod
    def _attach_config(msg: EmailMessage, config: Config) -> None:
        """Кладёт файл конфига вложением, угадывая MIME-тип по имени файла."""
        filename = config.download_filename
        ctype, _ = mimetypes.guess_type(filename)
        maintype, _, subtype = (ctype or "application/octet-stream").partition("/")
        msg.add_attachment(config.content, maintype=maintype, subtype=subtype, filename=filename)

    def _build_message(
        self, campaign: Campaign, recipient: Recipient, configs: list[Config]
    ) -> EmailMessage:
        """Собирает EmailMessage: текст кампании и файлы конфигов вложениями."""
        msg = EmailMessage()
        msg["From"] = self.settings.SMTP_USER
        msg["To"] = self._format_to(recipient)
        msg["Subject"] = campaign.subject
        msg.set_content(campaign.body)

        for config in configs:
            # Конфиг без файла пропускаем: до отправки такой кампании дело не дойдёт,
            # её не пропустит validate_campaign_ready.
            if config.content is not None:
                self._attach_config(msg, config)

        return msg

    @staticmethod
    def _is_temporary(exc: Exception) -> bool:
        """Временная ли ошибка (стоит повторить) или постоянная."""
        if isinstance(exc, (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError)):
            return True
        if isinstance(exc, smtplib.SMTPResponseException):
            return 400 <= exc.smtp_code < 500
        return isinstance(exc, (TimeoutError, ConnectionError, OSError))

    # ------------------------------------------------------------------ #
    # Публичное API
    # ------------------------------------------------------------------ #

    def _send_once(self, msg: EmailMessage) -> None:
        """Одна попытка отправки: соединение, письмо, гарантированное закрытие."""
        smtp = None
        try:
            smtp = self._connect()
            smtp.send_message(msg)
        finally:
            if smtp is not None:
                with contextlib.suppress(Exception):
                    smtp.quit()

    def _wait_before_retry(self, exc: Exception, attempt: int) -> None:
        """Экспоненциальная пауза между попытками: 2, 4, 8 секунд."""
        delay = 2**attempt
        log.warning(
            "Временная ошибка (%s), попытка %d/%d, пауза %d с",
            exc,
            attempt,
            self.settings.RETRIES,
            delay,
        )
        time.sleep(delay)

    def send(
        self, campaign: Campaign, recipient: Recipient, configs: list[Config]
    ) -> tuple[bool, str | None]:
        """Отправляет письмо с ретрами.

        Возвращает (успех, текст_ошибки). При постоянной ошибке (5xx, отказ
        получателя/отправителя) возвращает неуспех сразу, без повторов.
        """
        msg = self._build_message(campaign, recipient, configs)
        last_exc: Exception | None = None

        for attempt in range(1, self.settings.RETRIES + 1):
            try:
                self._send_once(msg)
            except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused) as exc:
                return (False, str(exc))
            except Exception as exc:  # noqa: BLE001 - развилка по типу ниже
                last_exc = exc
                if not self._is_temporary(exc) or attempt == self.settings.RETRIES:
                    return (False, str(exc))
                self._wait_before_retry(exc, attempt)
            else:
                return (True, None)

        return (False, str(last_exc) if last_exc else "unknown error")
