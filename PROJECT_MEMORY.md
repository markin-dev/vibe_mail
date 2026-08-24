# Память проекта vibe_mail

Живой журнал решений и прогресса по сессиям. Коммитится вместе с кодом.
Обновляй при каждом значимом решении или завершённом шаге реализации.

## Цель
Превратить утилиту рассылки `send_mail.py` (CLI) в полноценное приложение с HTTP API
на FastAPI. Позже поверх API появится фронтенд, который будет с ним работать.

## Принятые архитектурные решения (согласованы с пользователем)
- **Фреймворк:** FastAPI.
- **Хранение:** SQLite + SQLAlchemy 2.x (файл `vibe_mail.db`, gitignored). Статусы
  получателей в БД заменяют старый `sent.log` (это и есть механизм возобновления).
- **SMTP:** глобально из `.env` (`SMTP_*` в `app/core/config.py`) — один отправитель
  на всё приложение.
- **Auth:** нет (локальное приложение, доверенная сеть).
- **Отправка:** последовательно в фоновом потоке внутри процесса
  (`app/services/worker.py`), запущенном в `lifespan` приложения. БД — источник
  правды для возобновления после падения.
- **CLI:** только API, отдельного CLI-скрипта нет (решено отказаться).
- **Тесты:** не пишем (пользователь явно отменил).
- **Миграции:** Alembic НЕ подключаем на старте — `Base.metadata.create_all` при старте
  приложения. Alembic добавим позже, когда схема стабилизируется и появятся данные.
- **Запуск:** `python -m app` (через `app/__main__.py`) И `make dev` (Makefile).
  Uvicorn — `uvicorn[standard]`.
- **Менеджер пакетов:** Pipenv. `Pipfile` + `Pipfile.lock` — источник истины по
  зависимостям (старый `requirements.txt` удалён). Локальный venv создаётся в `.venv/`
  через `PIPENV_VENV_IN_PROJECT=1` (gitignored).
- **`.vscode/`:** добавлен в `.gitignore` — пользователь не хочет коммитить настройки
  редактора (каждый настраивает интерпретатор локально).

## Почему нельзя оставить синхронную отправку из CLI
В API запрос не может блокировать на всю рассылку: таймаут клиента, блокировка
воркеров Uvicorn, нет прогресса для фронта, нет отмены/возобновления. Поэтому
`start` отдаёт `202 Accepted`, а реальную отправку делает фоновый поток, обновляя
статусы в БД. Фронт опрашивает `GET /campaigns/{id}`.

## Целевая структура
```
app/
  main.py            # FastAPI app + lifespan (create_all, старт/стоп воркера)
  __main__.py        # python -m app -> uvicorn.run("app.main:app", ...)
  core/              # config.py (Settings), constants.py (EMAIL_RE), logging.py
  db/                # base.py (Base), session.py (engine, get_db), models.py
  schemas/           # campaign.py, recipient.py (pydantic-модели)
  services/          # mail_sender.py (MailSender), recipient_service, campaign_service, worker
  api/               # deps.py, campaigns.py, recipients.py, attachments.py, health.py
Makefile
Pipfile / Pipfile.lock
PROJECT_MEMORY.md    # эта память
```

## Инварианты (сохранять из оригинала send_mail.py)
- **Валидация ДО отправки:** синтаксис email (`EMAIL_RE`), дубликаты в рамках кампании,
  наличие/читаемость файлов, лимит вложений 25 МБ × 1.37 (base64 overhead). При ошибке —
  список проблем, ничего не отправляем.
- **Возобновление:** `sent` пропускаем; при старте процесса «зависшие» running-кампании
  подхватываются воркером.
- **Ретраи:** временные ошибки (4xx, обрыв, таймаут) — до 3 попыток с паузой 2/4/8 с и
  переподключением; постоянные (5xx, отказ получателя/отправителя) — `failed`, рассылка
  продолжается.
- Относительные пути вложений резолвятся относительно `ATTACHMENTS_DIR`.

## Прогресс реализации (по шагам)
- [x] **Шаг 1** — каркас: `app/__init__.py`, `app/core/*` (config, constants, logging);
  Pipenv-конфиг (`Pipfile`, `Pipfile.lock`), `requirements.txt` удалён.
- [x] **Шаг 2** — `app/db/` (base, session, models) + `app/__main__.py`. Таблицы
  `campaigns` / `recipients` / `attachments` создаются через `create_all`.
- [x] **Шаг 3** — `app/schemas/` (campaign.py, recipient.py): CampaignCreate/Read,
  RecipientCreate/Read, RecipientsBulk, AttachmentRead, MessageOut.
- [x] **Шаг 4** — `app/services/mail_sender.py`: класс `MailSender` (connect, build,
  retry 2/4/8 с, is_temporary). Не зависит от БД.
- [x] **Шаг 5** — `app/services/recipient_service.py` + `app/services/campaign_service.py`
  (валидация email/дубликаты/файлы/размер, CRUD, импорт CSV из `import_csv.py`).
- [x] **Шаг 6** — `app/services/worker.py` (фоновый поток) + `lifespan` в `app/main.py`.
- [ ] **Шаг 7** — `app/api/` роутеры (campaigns, recipients, attachments, health) +
  сборка `app/main.py`.
- [ ] **Шаг 8** — `Makefile`, `.env.example` (SMTP_*, DATABASE_URL, ATTACHMENTS_DIR).
- [ ] **Шаг 9** — обновить `README.md` под запуск `python -m app` / `make dev` и эндпоинты.

## Окружение / запуск
- Python 3.14.6 через pyenv.
- Установка зависимостей: `pip install pipenv` (в pyenv-python), затем
  `PIPENV_VENV_IN_PROJECT=1 pipenv install`.
- Локальный запуск: `pipenv run python -m app` (или `pipenv shell` → `python -m app`),
  либо `make dev` (после Шага 8).
- VS Code: выбрать интерпретатор `./.venv/bin/python` (Python: Select Interpreter),
  иначе Pylance ругается на импорты. `.vscode` в `.gitignore`.

## Заметки
- Глобальные правила из `~/.claude/CLAUDE.md` про TypeScript/Vue к этому Python-проекту
  не относятся (зафиксировано в AGENTS.md).
- Оригинальные `send_mail.py` / `import_csv.py` пока в репозитории: их логика
  переносится в `app/services/*`; после переноса можно удалить/пометить устаревшими.
- `app/__main__.py` импортирует `app.main`, которого ещё нет — `python -m app`
  заработает только после Шага 7 (создание `app/main.py`).
