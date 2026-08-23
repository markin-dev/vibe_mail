#!/usr/bin/env python3
"""Рассылка писем с индивидуальными вложениями по списку из YAML-конфига."""

import argparse
import logging
import mimetypes
import os
import re
import smtplib
import ssl
import sys
import time
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr, parseaddr
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Нужен PyYAML: pip install PyYAML (или apt install python3-yaml)")

MAX_ATTACHMENT_BYTES = 25 * 1024 * 1024
BASE64_OVERHEAD = 1.37
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
RETRIES = 3

log = logging.getLogger("vibe_mail")


# --------------------------------------------------------------------------- #
# Конфиг и окружение
# --------------------------------------------------------------------------- #

def load_env(path=".env"):
    """Читает .env в os.environ, не затирая уже заданные переменные."""
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)


def load_config(path):
    p = Path(path)
    if not p.is_file():
        sys.exit(f"Конфиг не найден: {p}")
    try:
        cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        sys.exit(f"Ошибка разбора YAML в {p}:\n{exc}")
    if not isinstance(cfg, dict):
        sys.exit(f"Конфиг {p} должен быть словарём верхнего уровня")

    errors = []
    smtp = cfg.get("smtp")
    if not isinstance(smtp, dict):
        errors.append("отсутствует секция smtp")
    else:
        for key in ("host", "port", "user"):
            if not smtp.get(key):
                errors.append(f"не задан smtp.{key}")
    for key in ("subject", "body"):
        if not cfg.get(key):
            errors.append(f"не задан {key}")
    recipients = cfg.get("recipients")
    if not isinstance(recipients, list) or not recipients:
        errors.append("recipients должен быть непустым списком")
    if errors:
        sys.exit("Ошибки конфига:\n  - " + "\n  - ".join(errors))

    cfg.setdefault("attachments_dir", "attachments")
    cfg.setdefault("delay", 2)
    cfg.setdefault("from_name", None)
    cfg.setdefault("body_html", None)
    return cfg


def validate(cfg, base_dir):
    """Проверяет адреса и вложения. Возвращает список нормализованных получателей."""
    errors = []
    att_dir = (base_dir / cfg["attachments_dir"]).resolve()
    seen = {}
    prepared = []

    for idx, raw in enumerate(cfg["recipients"], start=1):
        if isinstance(raw, str):
            raw = {"email": raw, "attachments": []}
        if not isinstance(raw, dict):
            errors.append(f"recipients[{idx}]: ожидался словарь или строка")
            continue

        email = str(raw.get("email", "")).strip()
        if not email or not EMAIL_RE.match(parseaddr(email)[1] or email):
            errors.append(f"recipients[{idx}]: некорректный адрес {email!r}")
            continue
        key = email.lower()
        if key in seen:
            errors.append(f"recipients[{idx}]: дубликат адреса {email} (уже в строке {seen[key]})")
            continue
        seen[key] = idx

        files, total = [], 0
        att = raw.get("attachments") or []
        if isinstance(att, str):
            att = [att]
        for name in att:
            path = Path(name)
            if not path.is_absolute():
                path = att_dir / path
            if not path.is_file():
                errors.append(f"{email}: файл не найден — {path}")
                continue
            if not os.access(path, os.R_OK):
                errors.append(f"{email}: нет прав на чтение — {path}")
                continue
            size = path.stat().st_size
            total += size
            files.append(path)

        if total * BASE64_OVERHEAD > MAX_ATTACHMENT_BYTES:
            errors.append(
                f"{email}: вложения весят {human(total)} "
                f"(~{human(int(total * BASE64_OVERHEAD))} после кодирования), "
                f"лимит {human(MAX_ATTACHMENT_BYTES)}"
            )

        prepared.append({"email": email, "name": raw.get("name"), "files": files, "size": total})

    if errors:
        sys.exit("Проверка не пройдена, ничего не отправлено:\n  - " + "\n  - ".join(errors))
    return prepared


def human(num):
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if num < 1024 or unit == "ГБ":
            return f"{num:.0f} {unit}" if unit == "Б" else f"{num:.1f} {unit}"
        num /= 1024


# --------------------------------------------------------------------------- #
# Журнал отправленных
# --------------------------------------------------------------------------- #

def load_sent(log_path):
    p = Path(log_path)
    if not p.is_file():
        return set()
    sent = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[2] == "OK":
            sent.add(parts[1].lower())
    return sent


def record_sent(handle, email):
    handle.write(f"{datetime.now().isoformat(timespec='seconds')}\t{email}\tOK\n")
    handle.flush()


# --------------------------------------------------------------------------- #
# Письмо и SMTP
# --------------------------------------------------------------------------- #

def build_message(cfg, recipient):
    msg = EmailMessage()
    sender = cfg["smtp"]["user"]
    msg["From"] = formataddr((cfg["from_name"], sender)) if cfg["from_name"] else sender
    msg["To"] = (
        formataddr((recipient["name"], recipient["email"]))
        if recipient.get("name")
        else recipient["email"]
    )
    msg["Subject"] = cfg["subject"]
    msg.set_content(cfg["body"])
    if cfg["body_html"]:
        msg.add_alternative(cfg["body_html"], subtype="html")

    for path in recipient["files"]:
        ctype, _ = mimetypes.guess_type(path.name)
        maintype, _, subtype = (ctype or "application/octet-stream").partition("/")
        msg.add_attachment(
            path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name
        )
    return msg


def connect_smtp(cfg, password, verbose=False):
    smtp_cfg = cfg["smtp"]
    host, port = smtp_cfg["host"], int(smtp_cfg["port"])
    context = ssl.create_default_context()
    use_ssl = smtp_cfg.get("use_ssl", port == 465)

    log.debug("Подключение к %s:%s (%s)", host, port, "SSL" if use_ssl else "STARTTLS")
    if use_ssl:
        smtp = smtplib.SMTP_SSL(host, port, context=context, timeout=30)
    else:
        smtp = smtplib.SMTP(host, port, timeout=30)
        smtp.ehlo()
        if smtp_cfg.get("use_tls", True):
            smtp.starttls(context=context)
            smtp.ehlo()
    if verbose:
        smtp.set_debuglevel(1)
    smtp.login(smtp_cfg["user"], password)
    log.info("Подключено к %s:%s как %s", host, port, smtp_cfg["user"])
    return smtp


def is_temporary(exc):
    if isinstance(exc, (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError)):
        return True
    if isinstance(exc, smtplib.SMTPResponseException):
        return 400 <= exc.smtp_code < 500
    return isinstance(exc, (TimeoutError, ConnectionError, OSError))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def parse_args():
    ap = argparse.ArgumentParser(
        description="Рассылка писем с индивидуальными вложениями по YAML-списку."
    )
    ap.add_argument("--config", default="config.yaml", help="путь к YAML-конфигу")
    ap.add_argument("--env", default=".env", help="файл с SMTP_PASSWORD")
    ap.add_argument("--dry-run", action="store_true", help="только показать, что будет отправлено")
    ap.add_argument("--delay", type=float, help="пауза между письмами, сек (перекрывает конфиг)")
    ap.add_argument("--log", default="sent.log", help="журнал отправленных")
    ap.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        help="не пропускать адреса из журнала",
    )
    ap.add_argument("--limit", type=int, help="отправить не больше N писем")
    ap.add_argument("--only", help="отправить только этому адресу")
    ap.add_argument("-v", "--verbose", action="store_true", help="подробный лог, включая SMTP")
    return ap.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )

    load_env(args.env)
    cfg = load_config(args.config)
    base_dir = Path(args.config).resolve().parent
    recipients = validate(cfg, base_dir)

    if args.only:
        target = args.only.lower()
        recipients = [r for r in recipients if r["email"].lower() == target]
        if not recipients:
            sys.exit(f"Адрес {args.only} не найден в конфиге")

    sent_before = load_sent(args.log) if args.resume else set()
    queue, skipped = [], []
    for r in recipients:
        (skipped if r["email"].lower() in sent_before else queue).append(r)
    if args.limit is not None:
        queue = queue[: args.limit]

    delay = args.delay if args.delay is not None else float(cfg["delay"])
    total_size = sum(r["size"] for r in queue)
    log.info(
        "К отправке: %d писем (%s вложений), пропущено по журналу: %d, пауза %.1f с",
        len(queue), human(total_size), len(skipped), delay,
    )
    for r in skipped:
        log.debug("Пропуск (уже отправлено): %s", r["email"])

    if not queue:
        log.info("Отправлять нечего.")
        return 0

    if args.dry_run:
        for r in queue:
            files = ", ".join(p.name for p in r["files"]) or "(без вложений)"
            log.info("DRY-RUN → %s | %s | %s [%s]", r["email"], cfg["subject"], files, human(r["size"]))
        log.info("Dry-run завершён, письма не отправлялись.")
        return 0

    password = os.environ.get("SMTP_PASSWORD")
    if not password:
        sys.exit("Не задан SMTP_PASSWORD (в .env или переменной окружения)")

    ok, failed = [], []
    smtp = connect_smtp(cfg, password, args.verbose)
    log_handle = open(args.log, "a", encoding="utf-8")

    try:
        for idx, r in enumerate(queue, start=1):
            msg = build_message(cfg, r)
            for attempt in range(1, RETRIES + 1):
                try:
                    smtp.send_message(msg)
                    record_sent(log_handle, r["email"])
                    ok.append(r["email"])
                    log.info(
                        "[%d/%d] Отправлено: %s (%d влож., %s)",
                        idx, len(queue), r["email"], len(r["files"]), human(r["size"]),
                    )
                    break
                except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused) as exc:
                    failed.append((r["email"], str(exc)))
                    log.error("[%d/%d] Отказ сервера для %s: %s", idx, len(queue), r["email"], exc)
                    break
                except Exception as exc:  # noqa: BLE001 - решаем по типу ниже
                    if not is_temporary(exc) or attempt == RETRIES:
                        failed.append((r["email"], str(exc)))
                        log.error("[%d/%d] Ошибка для %s: %s", idx, len(queue), r["email"], exc)
                        break
                    pause = 2 ** attempt
                    log.warning(
                        "Временная ошибка (%s), попытка %d/%d, пауза %d с",
                        exc, attempt, RETRIES, pause,
                    )
                    time.sleep(pause)
                    try:
                        smtp.quit()
                    except Exception:  # noqa: BLE001
                        pass
                    smtp = connect_smtp(cfg, password, args.verbose)

            if idx < len(queue) and delay > 0:
                time.sleep(delay)
    except KeyboardInterrupt:
        log.warning("Прервано пользователем.")
    finally:
        log_handle.close()
        try:
            smtp.quit()
        except Exception:  # noqa: BLE001
            pass

    log.info("Итого: отправлено %d, пропущено %d, ошибок %d", len(ok), len(skipped), len(failed))
    for email, reason in failed:
        log.error("  FAILED %s — %s", email, reason)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
