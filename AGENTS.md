# AGENTS.md — vibe_mail

Путеводитель для AI-агента по проекту **vibe_mail**: архитектура, инварианты и конвенции.

> Глобальные правила из `~/.claude/CLAUDE.md` про TypeScript/Vue/Composables **не
> относятся** к Python-части репозитория, но **применяются** к фронтенду в `admin-front/`.

## Что это
HTTP-API сервис массовой рассылки писем. Клиент (фронтенд `admin-front`) создаёт
кампании, добавляет получателей, запускает рассылку; отправка идёт в фоне, прогресс
виден по статусам в БД.

## Стек

Бэкенд:
- **FastAPI** + **Uvicorn** (`uvicorn[standard]`); Swagger на `/docs`.
- **SQLAlchemy 2.x** (sync, `Mapped[...]`) + **SQLite** (`vibe_mail.db`, gitignored).
- **pydantic-settings** — конфиг из `.env`.
- **Pipenv** (`Pipfile` + `Pipfile.lock`), venv в `.venv/`.
- Линтер — **ruff** (конфиг в `pyproject.toml`): select E/W/F/I/UP/B/C4/SIM/RET/PTH/TC,
  ignore `E501` (длину держит форматтер) и `B008` (ложный позитив на `Depends()`).
- Язык комментариев и сообщений — **русский**.
- Тестов **нет** (пользователь явно отменил).

Фронтенд (`admin-front/`) — отдельный npm-проект, с Pipenv не связан:
- **Vite 8** + **Vue 3.5** (`<script setup>` + Composition API) + **TypeScript 5.x**.
- **shadcn-vue** поверх **Tailwind v4**, примитивы reka-ui, иконки `@lucide/vue`,
  тосты `vue-sonner`.
- Формы — `vee-validate` + `@vee-validate/zod` + `zod`. Роутер — vue-router 4.
- Стора нет (ни Pinia, ни Vuex): состояние живёт в композаблах и локальных `ref`.
- ESLint (flat config `admin-front/eslint.config.js`); в `ignores` — `dist/**`,
  `api-mocker/**`, `src/components/ui/**`, `src/apiService/types/vibe-mail.ts`.

## Структура
```
app/
  main.py            # FastAPI app + lifespan (create_all, старт/стоп воркера)
  __main__.py        # python -m app -> uvicorn.run("app.main:app", ...)
  core/              # config.py (Settings), constants.py (EMAIL_RE), logging.py
  db/                # base.py (Base), session.py (engine, get_db), models.py
  schemas/           # campaign.py, recipient.py, import_recipients.py,
                     # envelope.py (pydantic-модели + обёртка ApiEnvelope)
  services/          # mail_sender.py (MailSender), recipient_service.py,
                     # campaign_service.py, import_service.py, config_service.py,
                     # config_generator.py, worker.py, config_worker.py
  api/               # deps.py, campaigns.py, recipients.py, configs.py, health.py
seed_campaigns.py    # фейковые кампании/получатели/конфиги для локальной БД
Makefile
Pipfile / Pipfile.lock
.env.example         # SMTP_*, DATABASE_URL, CORS_ORIGINS

admin-front/src/
  apiService/        # httpClient.ts, index.ts (фасад), types/vibe-mail.ts (генерируется),
                     # campaigns/ и recipients/ — по папке на домен + adapters/
  composables/       # useApiService.ts, useToast.ts; data/ — по файлу на метод API
  components/        # проектные компоненты + AppLayout/; ui/ — сгенерированный shadcn
  pages/             # CampaignsPage, CreateCampaignPage, CampaignDetailsPage
  router/
```

## API (базовый префикс `/api`)
| Метод | Путь | Назначение |
|---|---|---|
| `GET` | `/api/health` | здоровье |
| `POST` | `/api/campaigns` | создать кампанию |
| `GET` | `/api/campaigns` | список + прогресс |
| `GET`  | `/api/campaigns/{id}` | кампания + счётчики |
| `POST` | `/api/campaigns/{id}/recipients` | добавить получателей (атомарно) |
| `GET` | `/api/campaigns/{id}/recipients` | список получателей |
| `POST` | `/api/campaigns/{id}/recipients/preview` | предпросмотр вставленного списка (dry-run) |
| `POST` | `/api/campaigns/{id}/recipients/import` | импорт вставленного списка (201, частичный) |
| `POST` | `/api/campaigns/{id}/configs/generate` | поставить конфиги без файла в очередь на генерацию (202) |
| `GET` | `/api/configs/{config_id}/download` | скачать файл конфига (бинарный ответ, без конверта) |
| `POST` | `/api/campaigns/{id}/start` | запуск рассылки (202) |
| `POST` | `/api/campaigns/{id}/stop` | пауза (статус → NEW) |
| `DELETE` | `/api/campaigns/{id}` | удалить кампанию (200, MessageOutEnvelope) |
| `DELETE` | `/api/recipients/{rid}` | удалить получателя (204, без тела) |

## Ключевые инварианты (сохранять)
- **Валидация ДО отправки**: синтаксис email (`EMAIL_RE` из `core/constants.py`) и
  дубликаты в кампании — при добавлении получателей; готовность кампании —
  `recipient_service.validate_campaign_ready` (есть получатели, у каждого есть конфиги и
  **у каждого конфига сгенерирован файл**). При ошибке `start` возвращает `400` со списком,
  ничего не шлём: письмо без вложений уже не переотправить.
- **Возобновление**: кампании со статусом `IN_PROGRESS` подхватываются воркером при
  старте процесса; получатели со статусом `PENDING` отправляются заново. Источник
  правды — статусы получателей в БД (`PENDING`/`SENT`/`FAILED`).
- **Статусы кампании** (`CampaignStatus`, `app/db/models.py`): `NEW` (при создании) →
  `start` переводит в `IN_PROGRESS`; `stop` возвращает в `NEW`; воркер по завершении всех
  получателей ставит `DONE`, а если хотя бы у одного статус `FAILED` —
  `DONE_WITH_ERRORS` («Завершена с ошибками»); `ERROR` — зарезервированный статус
  фатального сбоя кампании, сейчас нигде не выставляется. `DONE` и `DONE_WITH_ERRORS`
  терминальные — воркер подхватывает только `IN_PROGRESS`. В БД хранится имя enum
  (`NEW`/`IN_PROGRESS`/…), в API-ответе — значение (`new`/`in_progress`/…).
- **Импорт получателей**: формат вставки жёсткий — ровно две колонки через таб
  (`имя_конфига<TAB>почта`), как копируется диапазон из Google Sheets. Разбор — только в
  `services/import_service.py`; строки с одинаковой почтой группируются в одно письмо с
  несколькими конфигами. Импорт **частичный, не атомарный**: валидные строки сохраняются,
  проблемные возвращаются списком с номером строки и причиной (иначе одна строка без почты
  заблокировала бы весь список). Если почта уже есть в кампании, конфиги дописываются
  существующему получателю; повторное имя конфига не задваивается, поэтому повторный импорт
  того же списка безопасен.
- **Генерация конфигов**: кнопка на странице кампании только **ставит в очередь** — меняет
  статус конфигов без файла (`PENDING`/`FAILED`) на `QUEUED` и отдаёт 202. Файлы добывает
  отдельный фоновый поток `services/config_worker.py`: `QUEUED` → `GENERATING` → `READY`
  (или `FAILED` с текстом в `error`), коммит после каждого конфига. При старте процесса
  зависшие `GENERATING` возвращаются в `QUEUED`. Готовые конфиги повторный запуск не
  трогает — догенерируются только недостающие. Файл лежит в БД (`configs.content`, BLOB).
- **Письмо**: тело — только текст кампании, файлы конфигов уезжают **вложениями**
  (`MailSender._build_message`). Воркер отдаёт отправителю ORM-конфиги получателя, контент
  берётся из БД; конфиг без файла пропускается при сборке, но до отправки дело не дойдёт —
  такую кампанию не даст запустить валидация.
- **Ретраи**: временные ошибки — до 3 попыток с паузой 2/4/8 с и переподключением
  (`mail_sender._is_temporary`); постоянные — `failed`, рассылка продолжается.
- **Фоновая отправка**: `start` отдаёт `202`, отправляет отдельный поток
  (`services/worker.py`), запущенный в `lifespan`. Запрос не блокируется.
- **Схема БД**: Alembic не подключён, таблицы создаются `Base.metadata.create_all` в
  `lifespan`. Миграции писать не нужно — после правки моделей БД пересоздаётся
  (цель `remake_db` в `Makefile`).

## Модули — зоны ответственности
- `core/config.py` — `Settings` (pydantic-settings), `get_settings()` (кеш).
- `core/constants.py` — `EMAIL_RE`.
- `db/*` — ORM: `Campaign`, `Recipient`, `Config` (+ `ConfigStatus`) + сессия.
- `schemas/*` — pydantic-модели запрос/ответ (`from_attributes=True`).
- `services/mail_sender.py` — `MailSender`: connect/build/retry; в БД не ходит — получает
  готовые объекты кампании, получателя и его конфигов.
- `services/recipient_service.py` — валидация, добавление получателей, готовность.
- `services/campaign_service.py` — CRUD кампаний (создание/чтение/смена статуса/удаление), прогресс.
- `services/import_service.py` — разбор вставленного из таблицы списка (единственное место
  парсинга), предпросмотр и импорт получателей.
- `services/config_service.py` — постановка конфигов кампании в очередь, доступ к конфигу.
- `services/config_generator.py` — получение файла по имени конфига; **не знает про БД**,
  как `mail_sender`. Сейчас заглушка со случайным WireGuard-конфигом.
- `services/worker.py` — фоновый поток отправки.
- `services/config_worker.py` — фоновый поток генерации конфигов.
- `api/*` — роутеры FastAPI; `deps.py` даёт `get_db` и `get_worker`.

## Архитектура бэкенда
- **Слоистая структура.** Путь запроса: `api/*` (роутеры) → `services/*` (бизнес-логика)
  → `db` (ORM). Роутеры тонкие: валидируют вход pydantic-схемами, вызывают сервисы,
  оборачивают результат. Сервисы не зависят от HTTP (`mail_sender` не знает про БД).
- **Единая обёртка ответов.** Все JSON-эндпоинты данных возвращают
  `ApiEnvelope[T]` = `{status: 'success'|'error', result, error}`. Для каждого ответа —
  явный подкласс в `schemas/envelope.py` (`CampaignReadEnvelope`, `ImportPreviewEnvelope`,
  `MessageOutEnvelope`, …) ради стабильных имён в OpenAPI (generic даёт хешированные
  суффиксы). Роутеры возвращают `ok(result)`. Ошибки (HTTPException,
  RequestValidationError, необработанные) перехватываются в `main.py` и тоже
  оборачиваются в `{status:'error', result:null, error}`.
- **Новый эндпоинт** трогает по порядку: `db/models.py` → `schemas/*` (+ свой подкласс
  конверта) → `services/*` → `api/*` → регенерация типов фронта.
- **Auth** — нет (локальное приложение). **CORS** — `CORSMiddleware` в `app/main.py`,
  список origin в `CORS_ORIGINS` (по умолчанию `http://localhost:5173`): в dev фронт
  ходит на бэкенд напрямую через `VITE_API_BASE_URL`, vite-прокси убран.

## Архитектура фронтенда
- **Слой API — `src/apiService/`** (фасад с адаптерами):
  - `httpClient.ts` — низкоуровневый `fetch`-обёртчик; базовый URL из `VITE_API_BASE_URL`
    (по умолчанию `/api`); бросает ошибку при `!response.ok` или `status === 'error'`.
  - `types/vibe-mail.ts` — **генерируется** из бэкендного `/openapi.json` через
    `openapi-typescript` (скрипт `generate:api`), руками не правится. Wire-типы берутся
    отсюда (`components['schemas']`).
  - `index.ts` — корневой баррель: `apiService.campaigns.*`, `apiService.recipients.*`.
  - **На каждый домен своя папка**: `<domain>ApiTypes.ts` (доменные camelCase-типы +
    wire-типы), `apiService.ts` (методы домена), `adapters/`.
  - **Адаптеры**: для чтения — `campaignsListAdapter.ts`, `campaignsItemAdapter.ts`; для
    действий — verb-first (`createCampaignAdapter.ts`, `importRecipientsAdapter.ts`).
    Каждый дефолт-экспорт = `{ adaptParams, adaptResponseData }`: `adaptParams` маппит
    доменный вход → wire, `adaptResponseData` снимает обёртку `{status,result,error}` и
    переводит snake_case → camelCase.
  - **Поток вызова:** компонент/композабл → `apiService.<domain>.<method>(input)` →
    `adapter.adaptParams` → `httpClient` → `adapter.adaptResponseData`.
- **Композаблы** (`src/composables/`): базовый `useApiService` (`isLoading`/`data`/
  `execute`/`onDone`/`onError`, ошибки в консоль + тост) лежит в корне. Доменные — в
  `composables/data/`, по файлу на метод API, имя повторяет метод: `getCampaigns` →
  `useGetCampaigns` (возвращает `campaigns`/`getCampaigns`), действия verb-first:
  `importRecipients` → `useImportRecipients`. Каждый экспортирует свой `ERROR_MESSAGE`.
  Композаблы не вызывают lifecycle-хуки — `onMounted`/`onUnmounted` живут в страницах.

## Конвенции фронтенда
- **Стили наших компонентов — CSS Modules**, не Tailwind: `<style module>` и
  `:class="$style.foo"`. Tailwind остаётся только для сгенерированных
  `src/components/ui/**`, убирать его нельзя.
- **Имя корневого класса = имя компонента** в camelCase: `CampaignsTable.vue` →
  `.campaignsTable`, `CampaignDetailsPage.vue` → `.campaignDetailsPage`. Внутренние классы
  именуются по смыслу (`.headerRow`, `.infoCard`, `.statusNew`). Исключение —
  `SidebarMenu.vue`: его корень `<SidebarGroup>` без класса.
- **Токены темы — через CSS-переменные** (`var(--foreground)`, `var(--muted-foreground)`,
  `var(--destructive)`, `var(--border)`, `var(--radius-md)`); цвета статусных бейджей
  заданы литералами с тёмной веткой через `:global(.dark) .statusX`.
- **`!important` не используем**: стили SFC-модуля инжектятся после глобального Tailwind,
  поэтому при равной специфичности наш класс перебивает базовый вариант по порядку
  каскада, а тёмная ветка выигрывает по специфичности.
- **`src/components/ui/**` не правим руками** — CLI shadcn перезаписывает эти файлы.
  Компоненты добавляются через shadcn-vue CLI строго из каталога `admin-front`. Если
  сгенерированному компоненту нужен глобальный CSS (например `vue-sonner/style.css`), он
  импортируется в `src/style.css`, а не внутри `ui/**`.
- **UI-элементы — только из shadcn** (`@/components/ui/*`): свою вёрстку кнопок, инпутов
  и карточек из `div`/`button` не пишем.
- **Порядок блоков в `.vue`**: `<template>` → `<script setup lang="ts">` → `<style module>`.
- **`data-test`** — на всех интерактивных элементах и строках списков (по ним ищут в тестах).
- **Полинг** (`CampaignsPage.vue`, `CampaignDetailsPage.vue`): интервал 3 с, опрашиваем
  **только пока есть кампания в `in_progress`**; флаг `pollInFlight` защищает от
  наложения запросов; таймер снимается в `onUnmounted`; скелетоны показываются только при
  первой загрузке, фоновые тики обновляют данные тихо.
- **Комментарии**: не дублируем в комментариях то, что видно из имени файла и кода;
  комментируем только нетривиальную логику.

## Принятые решения и их причины
- **Конфиги вместо вложений.** Работа с файлами (модель `Attachment`, роутер вложений,
  импорт CSV, лимиты размера, легаси-CLI) вырезана из проекта целиком. Вместо неё —
  модель `Config` (`recipient_id` + `name`): пока это только имя конфига, которое уезжает
  в тело письма столбиком.
- **Файлы конфигов лежат в той же таблице** (`filename`, `content` BLOB, `size` в `configs`) —
  конфиги WireGuard весят единицы килобайт, отдельная сущность под файл не нужна.
- **Генерация вынесена в фоновый поток**, потому что реальный источник файлов — SSH к
  VPN-серверу: 30+ конфигов заблокировали бы HTTP-запрос. Очередь выражена статусом самого
  конфига, отдельного поля у кампании нет.
- **Формат вставки жёсткий** — ровно две колонки через таб. Именно так Google Sheets
  кладёт в буфер скопированный диапазон, а textarea принимает plain-text flavor. От
  альтернативных разделителей, третьей колонки, автоопределения порядка колонок и
  нечёткого матчинга отказались сознательно, чтобы не усложнять.
- **Парсинг только на бэке** — одно место (`services/import_service.py`). Он нормализует
  `\r\n` и невидимые символы (NBSP, zero-width, BOM) и **приводит почту к нижнему
  регистру** — в таком виде адрес и группируется, и сохраняется в БД, поэтому строки,
  отличающиеся только регистром, дают одного получателя и одно письмо.
- **Предпросмотр отделён от импорта**: `preview` — dry-run, ничего не пишет, и показывает
  только те конфиги, которых у получателя ещё нет (уже заведённые — отдельным полем
  `existing_configs`), чтобы цифры совпадали с тем, что реально добавится.
- **Первая колонка — имя конфига, а не человека**, поэтому при импорте `Recipient.name`
  остаётся `None` и в `To:` уходит голый адрес.

## Известные недоделки
- `services/config_generator.py` — **заглушка**: отдаёт случайный WireGuard-конфиг вместо
  обращения к VPN-серверу по SSH. Место замены помечено `TODO` в модуле.
- Ограничения на суммарный размер вложений нет: конфиги весят сотни байт, но при переходе
  на реальные файлы стоит вернуть проверку лимита письма в `validate_campaign_ready`.
- Диалог импорта (`AddRecipientsDialog.vue`) закрывается кликом мимо окна и чистит
  textarea — вставленный текст теряется. Отложено осознанно.
- В `Pipfile` остался `pyyaml` от удалённого легаси-CLI: в `app/` он больше не используется.
- В рабочей копии лежит каталог `attachments/` с тестовыми файлами от удалённой фичи
  вложений.
