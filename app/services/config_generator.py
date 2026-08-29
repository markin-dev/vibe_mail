"""Источники файлов конфигов.

Два режима, выбираются настройкой `CONFIG_SOURCE`:
- `ssh` — заходим по SSH на VPN-сервер и создаём клиента через API панели AmneziaWG;
- `fake` — заглушка со случайным конфигом, чтобы разрабатывать без доступа к серверу.

Модули не знают про БД: получают имя конфига, возвращают готовый файл. Работу с БД делает
`config_worker`.
"""

from __future__ import annotations

import base64
import json
import logging
import secrets
import shlex
import time
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

import paramiko

if TYPE_CHECKING:
    from app.core.config import Settings

log = logging.getLogger("vibe_mail.config_generator")


class ConfigSourceError(Exception):
    """Не удалось получить конфиг: нет связи, ошибка панели, дубликат имени."""


class ConfigSource(Protocol):
    """Общий интерфейс источника: по имени конфига отдаёт (имя файла, содержимое)."""

    def generate(self, name: str) -> tuple[str, bytes]: ...

    def close(self) -> None: ...


def _config_filename(name: str) -> str:
    """Имя файла без путей — защита от подстановки `../` в имени конфига."""
    return f"{Path(name).name}.conf"


class FakeConfigSource:
    """Заглушка: правдоподобный WireGuard-конфиг со случайными ключами."""

    # Имитация похода на сервер, чтобы прогресс генерации был виден в интерфейсе.
    DELAY = 0.4
    SERVER_PUBLIC_KEY = "Zx1nKX0m6cQqvJHrGF3lTt5yWb8aNdPeS7uAoV2gYkM="

    @staticmethod
    def _random_key() -> str:
        return base64.b64encode(secrets.token_bytes(32)).decode()

    def generate(self, name: str) -> tuple[str, bytes]:
        time.sleep(self.DELAY)

        content = (
            "[Interface]\n"
            f"PrivateKey = {self._random_key()}\n"
            f"Address = 10.8.0.{secrets.randbelow(253) + 2}/32\n"
            "DNS = 1.1.1.1\n"
            "\n"
            "[Peer]\n"
            f"PublicKey = {self.SERVER_PUBLIC_KEY}\n"
            f"PresharedKey = {self._random_key()}\n"
            "AllowedIPs = 0.0.0.0/0, ::/0\n"
            f"Endpoint = vpn.example.com:{secrets.randbelow(20000) + 40000}\n"
            "PersistentKeepalive = 25\n"
        )

        log.info("Сгенерирован фейковый конфиг %s", name)
        return (_config_filename(name), content.encode())

    def close(self) -> None:
        """Закрывать нечего — метод есть ради общего интерфейса."""


class SshVpnConfigSource:
    """Конфиги с VPN-сервера через API панели AmneziaWG.

    Панель слушает только localhost сервера, поэтому запросы к ней выполняем как `curl`
    внутри SSH-сессии. Соединение переиспользуется между конфигами и переподключается
    при обрыве — на пачке в три десятка конфигов это экономит столько же хендшейков.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: paramiko.SSHClient | None = None
        self._server_id: str | None = settings.VPN_SERVER_ID or None

    # ------------------------------------------------------------------ #
    # Внутреннее: SSH и запросы к панели
    # ------------------------------------------------------------------ #

    def _connect(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.settings.SSH_HOST,
            port=self.settings.SSH_PORT,
            username=self.settings.SSH_USER,
            password=self.settings.SSH_PASSWORD,
            timeout=self.settings.SSH_TIMEOUT,
            allow_agent=False,
            look_for_keys=False,
        )
        log.info("SSH-соединение с %s установлено", self.settings.SSH_HOST)
        return client

    def _ssh(self) -> paramiko.SSHClient:
        """Живое соединение: поднимает новое, если его нет или оно оборвалось."""
        transport = self._client.get_transport() if self._client else None
        if transport is not None and transport.is_active():
            return self._client

        self.close()
        try:
            self._client = self._connect()
        except Exception as exc:
            raise ConfigSourceError(f"Не удалось подключиться по SSH: {exc}") from exc

        return self._client

    def _run(self, command: str) -> str:
        client = self._ssh()
        try:
            _, stdout, stderr = client.exec_command(command, timeout=self.settings.SSH_TIMEOUT)
            out = stdout.read().decode()
            err = stderr.read().decode().strip()
            code = stdout.channel.recv_exit_status()
        except Exception as exc:
            raise ConfigSourceError(f"Ошибка выполнения команды на сервере: {exc}") from exc

        if code != 0:
            raise ConfigSourceError(f"Команда на сервере завершилась с кодом {code}: {err}")

        return out

    def _build_curl_command(self, url: str, payload: dict | None) -> str:
        """Команда curl к панели: с payload — POST с JSON-телом, иначе GET."""
        auth = f"{self.settings.VPN_API_USER}:{self.settings.VPN_API_PASSWORD}"
        parts = ["curl", "-sS", "--fail-with-body", "-u", auth]

        if payload is not None:
            parts += [
                "-X", "POST",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload, ensure_ascii=False),
            ]  # fmt: skip

        parts.append(url)
        return " ".join(shlex.quote(part) for part in parts)

    @staticmethod
    def _parse_json(raw: str) -> object:
        """Ответ панели как JSON; иначе — понятная ошибка с куском тела."""
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ConfigSourceError(f"Панель вернула не JSON: {raw[:200]}") from exc

    def _api(self, path: str, payload: dict | None = None) -> object:
        """Запрос к API панели через curl на сервере. С payload — POST, иначе GET."""
        url = f"{self.settings.VPN_API_URL.rstrip('/')}{path}"
        return self._parse_json(self._run(self._build_curl_command(url, payload)))

    # ------------------------------------------------------------------ #
    # Публичное API
    # ------------------------------------------------------------------ #

    @staticmethod
    def _pick_single_server(servers: object) -> str:
        """ID единственного сервера панели; иначе — объясняющая ошибка."""
        if not isinstance(servers, list) or not servers:
            raise ConfigSourceError("На панели нет ни одного сервера")

        if len(servers) > 1:
            names = ", ".join(f"{s.get('name')} ({s.get('id')})" for s in servers)
            raise ConfigSourceError(f"На панели несколько серверов, укажите VPN_SERVER_ID: {names}")

        return servers[0]["id"]

    def resolve_server_id(self) -> str:
        """ID сервера панели: из настроек либо единственный существующий."""
        if not self._server_id:
            self._server_id = self._pick_single_server(self._api("/api/servers"))
        return self._server_id

    def list_client_names(self) -> list[str]:
        clients = self._api(f"/api/servers/{self.resolve_server_id()}/clients")
        if not isinstance(clients, list):
            raise ConfigSourceError("Панель вернула неожиданный ответ на список клиентов")

        return [client["name"] for client in clients]

    def _create_client(self, server_id: str, name: str) -> str:
        """Создаёт клиента на панели и возвращает текст его конфига."""
        response = self._api(f"/api/servers/{server_id}/clients", {"name": name})
        if not isinstance(response, dict) or not response.get("config"):
            raise ConfigSourceError(f"Панель не вернула конфиг для {name}: {response}")

        return response["config"]

    def generate(self, name: str) -> tuple[str, bytes]:
        """Создаёт клиента на сервере и возвращает его конфиг.

        Дубликат имени — ошибка: молча переиспользовать чужого клиента нельзя, а плодить
        одноимённых пиров тем более.
        """
        server_id = self.resolve_server_id()

        if name in self.list_client_names():
            raise ConfigSourceError(f"Клиент {name} уже есть на VPN-сервере")

        config = self._create_client(server_id, name)
        log.info("Клиент %s создан на VPN-сервере", name)

        return (_config_filename(name), config.encode())

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None


def get_config_source(settings: Settings) -> ConfigSource:
    """Источник конфигов по настройке CONFIG_SOURCE."""
    if settings.CONFIG_SOURCE == "fake":
        log.warning("Источник конфигов — заглушка (CONFIG_SOURCE=fake)")
        return FakeConfigSource()

    return SshVpnConfigSource(settings)
