"""Сидинг БД: создаёт 15 кампаний с разными данными.

Запуск из корня репозитория:
    pipenv run python seed_campaigns.py

Таблицы создаются через Base.metadata.create_all (на случай пустой БД).
"""
import datetime

from sqlalchemy.orm import Session

from app.db.models import Base, Campaign, CampaignStatus
from app.db.session import SessionLocal, engine


def _days_ago(days: int) -> datetime.datetime:
    """Возвращает naive-UTC время на N дней назад от текущего момента."""
    base = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    return base - datetime.timedelta(days=days)


# (name, subject, body, from_name, status, created_at_days_ago)
SEED: list[tuple[str, str, str, str | None, CampaignStatus, int]] = [
    (
        "Новогодняя рассылка 2026",
        "С наступающим 2026 годом!",
        "Дорогой клиент, поздравляем вас с Новым годом и дарим скидку 20%.",
        "Команда Vibe",
        CampaignStatus.DONE,
        210,
    ),
    (
        "Запуск нового тарифа Pro",
        "Попробуйте Vibe Pro бесплатно 14 дней",
        "Мы запустили тариф Pro с расширенной аналитикой. Активируйте прямо сейчас.",
        "Маркетинг Vibe",
        CampaignStatus.RUNNING,
        1,
    ),
    (
        "Опрос удовлетворённости",
        "Помогите нам стать лучше — 2 минуты вашего времени",
        "Пройдите короткий опрос и получите промокод на следующий заказ.",
        None,
        CampaignStatus.PAUSED,
        12,
    ),
    (
        "Вебинар по массовым рассылкам",
        "Регистрируйтесь на бесплатный вебинар 15 сентября",
        "Разберём лучшие практики рассылок с индивидуальными вложениями.",
        "Обучение Vibe",
        CampaignStatus.DRAFT,
        3,
    ),
    (
        "Восстановление корзины",
        "Вы забыли товары в корзине 🛒",
        "Ваши товары всё ещё ждут вас. Завершите оформление со скидкой 10%.",
        "Магазин Vibe",
        CampaignStatus.DONE,
        45,
    ),
    (
        "Ежемесячный дайджест — август",
        "Что нового в Vibe за август",
        "Подборка обновлений, кейсов и полезных статей за прошедший месяц.",
        "Команда Vibe",
        CampaignStatus.DONE,
        30,
    ),
    (
        "Специальное предложение для партнёров",
        "Партнёрская программа: +15% к вознаграждению",
        "До конца месяца повышенный процент за привлечённых клиентов.",
        "Партнёрство Vibe",
        CampaignStatus.RUNNING,
        6,
    ),
    (
        "Техническое обслуживание API",
        "Плановые работы 1 сентября с 02:00 до 04:00",
        "Сообщаем о плановом обслуживании. Сервис будет временно недоступен.",
        "Поддержка Vibe",
        CampaignStatus.DONE,
        25,
    ),
    (
        "Приглашение на закрытую вечеринку",
        "Только для клиентов Premium",
        "Приглашаем вас на вечеринку для партнёров и VIP-клиентов.",
        "Vibe Events",
        CampaignStatus.ERROR,
        8,
    ),
    (
        "Обновление политики конфиденциальности",
        "Важные изменения в политике конфиденциальности",
        "Ознакомьтесь с обновлёнными условиями обработки данных.",
        "Юристы Vibe",
        CampaignStatus.DONE,
        60,
    ),
    (
        "Летняя распродажа — скидки до 50%",
        "Летние скидки в приложении Vibe",
        "Успейте купить по сниженным ценам до конца сезона.",
        "Магазин Vibe",
        CampaignStatus.DONE,
        75,
    ),
    (
        "Welcome-серия: шаг 1 из 3",
        "Добро пожаловать в Vibe! Начнём с основ",
        "Краткое руководство для новых пользователей: первые шаги в сервисе.",
        None,
        CampaignStatus.PAUSED,
        2,
    ),
    (
        "Напоминание об оплате подписки",
        "Ваша подписка истекает через 3 дня",
        "Продлите подписку, чтобы не потерять накопленные данные.",
        "Биллинг Vibe",
        CampaignStatus.RUNNING,
        0,
    ),
    (
        "Кейс: как мы ускорили отправку в 3 раза",
        "Инженерный разбор фоновой рассылки",
        "Рассказываем, как архитектура на FastAPI ускорила доставку писем.",
        "Инженеры Vibe",
        CampaignStatus.DRAFT,
        18,
    ),
    (
        "Поздравление с профессиональным праздником",
        "С днём программиста!",
        "Поздравляем всех разработчиков с профессиональным праздником!",
        "Команда Vibe",
        CampaignStatus.DONE,
        15,
    ),
]


def seed(db: Session) -> int:
    Base.metadata.create_all(engine)
    count = 0
    for name, subject, body, from_name, status, days in SEED:
        campaign = Campaign(
            name=name,
            subject=subject,
            body=body,
            from_name=from_name,
            status=status,
            created_at=_days_ago(days),
        )
        db.add(campaign)
        count += 1
    db.commit()
    return count


def main() -> None:
    db = SessionLocal()
    try:
        created = seed(db)
        print(f"Создано кампаний: {created}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
