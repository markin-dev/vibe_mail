"""Настройка логирования.

Используем модуль logging, а не print (кроме служебных сводок в API).
"""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Конфигурирует базовый вывод логов в stdout."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
