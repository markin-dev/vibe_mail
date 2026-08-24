"""Отправка писем через SMTP.

Инкапсулирует всю работу с smtplib: подключение (SSL/STARTTLS), сборку
письма, ретраи с переподключением. Не знает про базу данных — получает
готовые объекты кампании/получателя и пути к файлам вложений.
"""
from __future__ import annotations

import logging
import mimetypes
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path

from app.core.config import Settings
from app.db.models import Campaign, Recipient

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

    def _build_message(
        self, campaign: Campaign, recipient: Recipient, files: list[Path]
    ) -> EmailMessage:
        """Собирает EmailMessage из данных кампании и получателя."""
        sender = self.settings.SMTP_USER
        msg = EmailMessage()
        msg["From"] = formataddr((campaign.from_name, sender)) if campaign.from_name else sender
        msg["To"] = (
            formataddr((recipient.name, recipient.email))
            if recipient.name
            else recipient.email
        )
        msg["Subject"] = campaign.subject
        msg.set_content(campaign.body)
        if campaign.body_html:
            msg.add_alternative(campaign.body_html, subtype="html")

        for path in files:
            ctype, _ = mimetypes.guess_type(path.name)
            maintype, _, subtype = (ctype or "application/octet-stream").partition("/")
            msg.add_attachment(
                path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name
            )
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

    def send(
        self, campaign: Campaign, recipient: Recipient, files: list[Path]
    ) -> tuple[bool, str | None]:
        """Отправляет письмо с ретрами.

        Возвращает (успех, текст_ошибки). При постоянной ошибке (5xx, отказ
        получателя/отправителя) возвращает неуспех сразу, без повторов.
        """
        msg = self._build_message(campaign, recipient, files)
        last_exc: Exception | None = None

        for attempt in range(1, self.settings.RETRIES + 1):
            smtp = None
            try:
                smtp = self._connect()
                smtp.send_message(msg)
                return (True, None)
            except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused) as exc:
                return (False, str(exc))
            except Exception as exc:  # noqa: BLE001 - развилка по типу ниже
                last_exc = exc
                if not self._is_temporary(exc) or attempt == self.settings.RETRIES:
                    return (False, str(exc))
                log.warning(
                    "Временная ошибка (%s), попытка %d/%d, пауза %d с",
                    exc, attempt, self.settings.RETRIES, 2 ** attempt,
                )
                time.sleep(2 ** attempt)
            finally:
                if smtp is not None:
                    try:
                        smtp.quit()
                    except Exception:  # noqa: BLE001
                        pass

        return (False, str(last_exc) if last_exc else "unknown error")
