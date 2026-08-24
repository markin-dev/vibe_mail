# AGENTS.md — vibe_mail

Путеводитель для AI-агента по проекту **vibe_mail**.

> Проект на **Python 3** (FastAPI + SQLAlchemy + PyYAML). Глобальные правила из
> `~/.claude/CLAUDE.md`, касающиеся TypeScript/Vue/Composables, к этому
> репозиторию не относятся — применяются только общепроектные принципы.

> **Память проекта** (решения, прогресс реализации и контекст сессий) хранится в
> `PROJECT_MEMORY.md` в этом же репозитории — коммить её вместе с кодом и обновляй
> при значимых изменениях.

## Что это
HTTP-API сервис массовой рассылки писем с индивидуальными вложениями. Клиент
(позже — фронтенд) создаёт кампании, добавляет получателей и вложения, запускает
рассылку; отправка идёт в фоне, прогресс виден по статусам в БД.

## Стек и конвенции
- **FastAPI** + **Uvicorn** (`uvicorn[standard]`); документация Swagger на `/docs`.
- **SQLAlchemy 2.x** (sync) + **SQLite** (`vibe_mail.db`, gitignored).
- **pydantic-settings** — конфиг из `.env`; **python-multipart** — загрузка файлов.
- **Pipenv**: `Pipfile` + `Pipfile.lock` — источник зависимостей (бывший
  `requirements.txt` удалён). Локальный venv в `.venv/` (через
  `PIPENV_VENV_IN_PROJECT=1`, gitignored).
- Язык комментариев и сообщений — **русский**.
- Тестов **нет** (пользователь явно отменил).
- Правила глобального `CLAUDE.md` про TS/Vue не применять.

## Структура (реализовано)
```
app/
  main.py            # FastAPI app + lifespan (create_all, старт/стоп воркера)
  __main__.py        # python -m app -> uvicorn.run("app.main:app", ...)
  core/              # config.py (Settings), constants.py (EMAIL_RE), logging.py
  db/                # base.py (Base), session.py (engine, get_db), models.py
  schemas/           # campaign.py, recipient.py (pydantic-модели)
  services/          # mail_sender.py (MailSender), recipient_service.py,
                     # campaign_service.py, worker.py
  api/               # deps.py, campaigns.py, recipients.py, attachments.py, health.py
Makefile             # make dev / make run / make install
Pipfile / Pipfile.lock
.env.example         # SMTP_*, DATABASE_URL, ATTACHMENTS_DIR
PROJECT_MEMORY.md    # журнал решений и прогресса
```

## Запуск (локально)
```bash
pip install pipenv
PIPENV_VENV_IN_PROJECT=1 pipenv install
cp .env.example .env        # заполнить SMTP_PASSWORD
make dev                    # = pipenv run uvicorn app.main:app --reload
```
Альтернатива: `pipenv run python -m app [--host --port --reload]`.
В VS Code выбрать интерпретатор `./.venv/bin/python` (иначе Pylance ругается на импорты).

## API (базовый префикс `/api`)
| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/api/health` | здоровье |
| `POST` | `/api/campaigns` | создать кампанию |
| `GET` | `/api/campaigns` | список + прогресс |
| `GET` | `/api/campaigns/{id}` | кампания + счётчики |
| `POST` | `/api/campaigns/{id}/recipients` | добавить получателей (атомарно) |
| `GET` | `/api/campaigns/{id}/recipients` | список получателей |
| `POST` | `/api/campaigns/{id}/import-csv` | импорт CSV (`имя,email,файл`) |
| `POST` | `/api/campaigns/{id}/recipients/{rid}/attachments` | загрузить вложение |
| `POST` | `/api/campaigns/{id}/start` | запуск рассылки (202) |
| `POST` | `/api/campaigns/{id}/stop` | пауза |
| `DELETE` | `/api/recipients/{rid}` | удалить получателя |

## Ключевые инварианты (сохранять)
- **Валидация ДО отправки**: `recipient_service.validate_campaign_ready` — синтаксис
  email (`EMAIL_RE` из `core/constants.py`), дубликаты в кампании, наличие/читаемость
  файлов, лимит вложений 25 МБ × 1.37. При ошибке `start` возвращает `400` со
  списком, ничего не шлём.
- **Возобновление**: статусы получателей в БД (`pending`/`sent`/`failed`) заменяют
  старый `sent.log`. Воркер при старте процесса подхватывает «зависшие» `RUNNING`.
- **Ретраи**: временные ошибки — до 3 попыток с паузой 2/4/8 с и переподключением
  (`mail_sender._is_temporary`); постоянные — `failed`, рассылка продолжается.
- **Фоновая отправка**: `start` отдаёт `202`, отправляет отдельный поток
  (`services/worker.py`), запущенный в `lifespan`. Запрос не блокируется.

## Модули — зоны ответственности
- `core/config.py` — `Settings` (pydantic-settings), `get_settings()` (кеш).
- `core/constants.py` — `EMAIL_RE`.
- `db/*` — ORM: `Campaign`, `Recipient`, `Attachment` + сессия.
- `schemas/*` — pydantic-модели запрос/ответ (`from_attributes=True`).
- `services/mail_sender.py` — `MailSender`: connect/build/retry; **не знает про БД**.
- `services/recipient_service.py` — валидация, добавление, вложения, готовность.
- `services/campaign_service.py` — CRUD кампаний, прогресс, импорт CSV.
- `services/worker.py` — фоновый поток отправки.
- `api/*` — роутеры FastAPI; `deps.py` даёт `get_db` и `get_worker`.

## Заметки
- `send_mail.py` / `import_csv.py` — **легаси** CLI; логика перенесена в
  `app/services/*`. Удалять только после проверки нового API.
- Миграции: Alembic пока **не подключён** — таблицы создаются
  `Base.metadata.create_all` в `lifespan`. Добавить Alembic, когда схема
  стабилизируется.
- `.vscode/` в `.gitignore` (настройки редактора не коммитим).
