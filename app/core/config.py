"""Настройки приложения vibe_mail.

Читаются из переменных окружения и файла `.env` (через pydantic-settings).
Пароль SMTP — только здесь (SMTP_PASSWORD), в конфиг не попадает.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- SMTP (глобальный отправитель на всё приложение) ---
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    # --- База данных ---
    DATABASE_URL: str = "sqlite:///./vibe_mail.db"

    # --- Лимиты отправки ---
    RETRIES: int = 3
    DEFAULT_DELAY: float = 2.0

    # --- Источник конфигов ---
    # ssh — ходим на VPN-сервер, fake — заглушка со случайным конфигом (разработка).
    CONFIG_SOURCE: str = "ssh"

    # --- SSH к VPN-серверу ---
    SSH_HOST: str = ""
    SSH_PORT: int = 22
    SSH_USER: str = ""
    SSH_PASSWORD: str = ""
    SSH_TIMEOUT: int = 30

    # --- API панели AmneziaWG (слушает localhost на VPN-сервере) ---
    VPN_API_URL: str = "http://127.0.0.1:8080"
    VPN_API_USER: str = ""
    VPN_API_PASSWORD: str = ""
    # Пусто — берём единственный сервер панели.
    VPN_SERVER_ID: str = ""

    # --- CORS (фронт в dev на отдельном порту, Vite :5173) ---
    # Через запятую; пустое значение (например, пустая env-переменная) — взять умолчание.
    CORS_ORIGINS: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    """Возвращает кешированный синглтон настроек."""
    return Settings()
