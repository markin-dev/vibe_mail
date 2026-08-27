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

## Архитектура

### Бэкенд (FastAPI)
- **Слоистая структура.** Путь запроса: `api/*` (роутеры) → `services/*` (бизнес-логика)
  → `db` (ORM). Роутеры тонкие: валидируют вход pydantic-схемами, вызывают сервисы,
  оборачивают результат. Сервисы не зависят от HTTP (`mail_sender` не знает про БД).
- **Единая обёртка ответов.** Все JSON-эндпоинты данных возвращают
  `ApiEnvelope[T]` = `{status: 'success'|'error', result, error}`. Для каждого ответа —
  явный подкласс в `schemas/envelope.py` (`CampaignReadEnvelope`,
  `ListCampaignReadEnvelope`, `MessageOutEnvelope`, …) ради стабильных имён в OpenAPI
  (generic даёт хешированные суффиксы). Роутеры возвращают `ok(result)`. Ошибки
  (HTTPException, RequestValidationError, необработанные) перехватываются в `main.py`
  и тоже оборачиваются в `{status:'error', result:null, error}`.
- **Конфиг** — `core/config.py` (`Settings` + кешированный `get_settings()`); SMTP и БД
  из `.env`. **Auth** — нет. **Миграции** — Alembic не подключён, таблицы создаются
  `Base.metadata.create_all` в `lifespan`.
- **Отправка** — фоновый поток `services/worker.py`, стартует в `lifespan`; подхватывает
  «зависшие» `RUNNING`. Статусы получателей в БД — механизм возобновления. Валидация ДО
  отправки — `recipient_service.validate_campaign_ready` (синтаксис email, дубликаты,
  размер вложений); при ошибке `start` отдаёт 400. Ретраи в `mail_sender` (2/4/8 с для
  временных ошибок).

### Фронтенд (admin-front)
- **Стек:** Vite 8 + Vue 3.5 (`<script setup>` + Composition API) + TypeScript 6,
  shadcn-vue поверх Tailwind v4. Node 24 (nvm). Глобальные правила `~/.claude/CLAUDE.md`
  (TS/Vue/Composables/тесты/импорты) **применяются**.
- **Слой API — `src/apiService/`** (фасадная архитектура с адаптерами):
  - `httpClient.ts` — низкоуровневый `fetch`-обёртчик. Базовый URL из `VITE_API_BASE_URL`
    (по умолчанию `/api`; в dev Vite проксирует `/api` → `http://localhost:8000`, поэтому
    CORS на бэкенде не нужен). Бросает ошибку при `!response.ok` или `status === 'error'`.
  - `types/vibe-mail.ts` — **сгенерировано** из бэкенд-`/openapi.json` через
    `openapi-typescript` (скрипт `npm run generate:api`, файл в `.eslintignore`).
    Wire-типы берутся отсюда (`components['schemas']`).
  - `index.ts` — **корневой баррель**: собирает доменные сервисы в единый фасад
    `apiService` (использование: `apiService.campaigns.getCampaigns()`).
  - **На каждый домен — своя папка** (например, `campaigns/`):
    - `campaignsApiTypes.ts` — доменные типы (camelCase, без обёртки) + wire-типы
      (из сгенерированной схемы).
    - `apiService.ts` — методы домена: вызывают `httpClient`, прогоняют параметры/ответ
      через адаптеры, возвращают доменные данные.
    - `adapters/` — `campaignsListAdapter.ts`, `campaignsItemAdapter.ts` и т.д. Каждый
      дефолт-экспорт = `{ adaptParams, adaptResponseData }`: `adaptParams` маппит доменные
      входные данные → wire (тело/query), `adaptResponseData` снимает обёртку
      `{status,result,error}` и маппит `result` → доменные типы (snake_case → camelCase).
  - **Поток вызова:** компонент/компосабл → `apiService.<domain>.<method>(input)` →
    `adapter.adaptParams(input)` → `httpClient.<method>` → `adapter.adaptResponseData(wire)`.
- **Компосаблы** (`src/composables/`): базовый `useApiService` (обёртка вызова API —
  `isLoading`/`data`/`execute`/`onDone`/`onError`; ошибки пишутся в консоль) лежит в корне
  `composables/`. Доменные компосаблы, работающие с API, лежат в `src/composables/data/` и
  строятся поверх `useApiService` + фасада `apiService`: в `useApiService` передаётся ссылка
  на метод API-сервиса, а название компосабла повторяет метод, напр. `getCampaigns` →
  `useGetCampaigns` (`campaigns: data`, `getCampaigns: execute`).
- **Страницы/компоненты** (`src/pages`, `src/components`): порядок блоков в `.vue` —
  `<template>` → `<script>` → `<style>`; UI только из shadcn (`@/components/ui`). Поиск в
  тестах — по `data-test`.

## Заметки
- `send_mail.py` / `import_csv.py` — **легаси** CLI; логика перенесена в
  `app/services/*`. Удалять только после проверки нового API.
- Миграции: Alembic пока **не подключён** — таблицы создаются
  `Base.metadata.create_all` в `lifespan`. Добавить Alembic, когда схема
  стабилизируется.
- `.vscode/` в `.gitignore` (настройки редактора не коммитим).
- **Фронтенд-админка** живёт в отдельном каталоге `admin-front/` (Vite 8 + Vue 3.5 +
  TypeScript 6, Node 24 через nvm). Это отдельный npm-проект, не связанный с
  Pipenv. Глобальные правила `~/.claude/CLAUDE.md` про TS/Vue **применяются** к нему.
  Запуск: `cd admin-front && npm install && npm run dev`. Подробности — в
  `PROJECT_MEMORY.md` (раздел «Фронтенд»).
- **UI-kit шадкн**: в `admin-front` проинициализирован **shadcn-vue** поверх **Tailwind
  CSS v4** (`@tailwindcss/vite`). Компоненты — исходники в `src/components/ui`,
  добавляются через `npx shadcn-vue@latest add <name>` (строго из `admin-front`).
  MCP `shadcnVue` в `opencode.json` настроен с `cwd: "admin-front"`. Корневые
  npm-артефакты, которые установщик скилла слил в корень, удалены — фронт полностью
  изолирован в `admin-front/`.
- **Порядок блоков в `.vue`-файлах (наши компоненты):** сначала `<template>`,
  затем `<script>` (`setup`), затем `<style>`. Относится к проектным файлам
  (`src/App.vue`, `src/components/*` кроме `ui/`, будущие страницы/компоненты).
  Сгенерированные shadcn-компоненты в `src/components/ui/*` не трогаем — их
  перезаписывает тулинг при обновлениях. Если сгенерированный компонент
  требует глобальный CSS (пример: `vue-sonner/style.css` для
  `src/components/ui/sonner`), этот CSS импортируем **глобально** в
  `src/style.css` через `@import 'vue-sonner/style.css';`, а НЕ внутри файлов
  `src/components/ui/**` (иначе правка слетит при следующем `shadcn-vue add`).
- **UI-элементы — только из shadcn:** кнопки берём из `@/components/ui/button`
  (`Button`), свою реализацию кнопок/инпутов/карточек не пишем. Любой элемент
  интерфейса — из shadcn (или добавляем через `npx shadcn-vue@latest add <name>`),
  а не кастомная вёрстка `div`/`button`.
- **Комментарии в фронтенде (`admin-front`):** избыточные комментарии не нужны. Не
  дублируй в комментариях в начале файла то, что и так понятно из имени файла и кода
  (назначение файла, очевидные шаги). Комментируй только нетривиальную логику.
