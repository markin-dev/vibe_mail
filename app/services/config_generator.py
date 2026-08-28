"""Получение файла конфига по его имени.

Сейчас это заглушка: отдаёт правдоподобный WireGuard-конфиг со случайным наполнением,
чтобы можно было проверить весь путь «кнопка → воркер → БД → таблица → скачивание».
Позже вместо генерации здесь появится обращение к API VPN-сервера по SSH.

Модуль не знает про БД — как и `mail_sender`: получает имя, возвращает готовый файл.
"""
import base64
import logging
import secrets
import time
from pathlib import Path

log = logging.getLogger("vibe_mail.config_generator")

# Имитация похода на VPN-сервер, чтобы прогресс генерации был виден в интерфейсе.
FAKE_DELAY = 0.4

SERVER_PUBLIC_KEY = "Zx1nKX0m6cQqvJHrGF3lTt5yWb8aNdPeS7uAoV2gYkM="


def _random_key() -> str:
    """Случайный ключ в том же формате, что и настоящий ключ WireGuard."""
    return base64.b64encode(secrets.token_bytes(32)).decode()


def _safe_filename(name: str) -> str:
    """Имя файла без путей — защита от подстановки `../` в имени конфига."""
    return f"{Path(name).name}.conf"


def generate_config(name: str) -> tuple[str, bytes]:
    """Возвращает (имя файла, содержимое конфига).

    TODO: заменить на получение конфига с VPN-сервера по SSH.
    """
    time.sleep(FAKE_DELAY)

    content = (
        "[Interface]\n"
        f"PrivateKey = {_random_key()}\n"
        f"Address = 10.8.0.{secrets.randbelow(253) + 2}/32\n"
        "DNS = 1.1.1.1\n"
        "\n"
        "[Peer]\n"
        f"PublicKey = {SERVER_PUBLIC_KEY}\n"
        f"PresharedKey = {_random_key()}\n"
        "AllowedIPs = 0.0.0.0/0, ::/0\n"
        f"Endpoint = vpn.example.com:{secrets.randbelow(20000) + 40000}\n"
        "PersistentKeepalive = 25\n"
    )

    log.info("Сгенерирован конфиг %s", name)
    return (_safe_filename(name), content.encode())
