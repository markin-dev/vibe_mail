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
- **Фронтенд (админка):** отдельный проект в каталоге `admin-front/` на **Vite 8 +
  Vue 3.5 + TypeScript ~5.9** (закреплён на 5.x — `openapi-typescript` несовместим с TS 6;
  стандартный scaffold `npm create vite` с шаблоном `vue-ts`). Node — **24** (через nvm:
  `nvm use 24`). К нему цепляется админка поверх HTTP API бэкенда. Глобальные правила
  из `~/.claude/CLAUDE.md` про TS/Vue **применяются** к `admin-front/` (в отличие от
  Python-части). Запуск: `cd admin-front && npm install && npm run dev`.

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

## Фронтенд (admin-front) — админка
- Каталог `admin-front/` — отдельный npm-проект (не зависит от Pipenv/Python).
- Стек: **Vite 8**, **Vue 3.5** (`<script setup>` + Composition API), **TypeScript ~5.9**
  (закреплён на 5.x — `openapi-typescript` пока не имеет TS-6-совместимой версии, при TS 6
  падает `npm install`). Проверка типов через `vue-tsc` в `npm run build`. Node 24 обязателен (nvm).
- **UI-kit — shadcn-vue**: проинициализирован внутри `admin-front` (`components.json`,
  `src/lib/utils.ts` с `cn()`, алиасы `@/*` → `./src/*`, `ui` → `@/components/ui`).
  Компоненты добавляются как исходники в `src/components/ui` через CLI
  `npx shadcn-vue@latest add <name>` (запускать строго из `admin-front`).
- **Tailwind CSS v4**: подключён через `@tailwindcss/vite`, директива
  `@import "tailwindcss";` в `src/style.css`; CSS-переменные темы (base color `neutral`,
  style `nova`) прописаны туда же шагом `init`.
- Правила из `~/.claude/CLAUDE.md` (TS/Vue/Composables/тесты/импорты) **действуют**
  для этого каталога. В частности: `withDefaults` для пропсов, type guards вместо
  `as`, компоненты без внешних margin, поиск по `data-test`, composables не вызывают
  lifecycle-хуки напрямую (возвращают функцию инициализации).
- **MCP shadcn-vue** (`opencode.json`) запускается с `cwd: "admin-front"`, чтобы
  инструменты MCP работали с фронтом, а не с корнем репозитория. Скилл
  `.agents/skills/shadcn-vue` — это инструкции; его команды тоже выполняются из
  `admin-front`.
- Корневые npm-артефакты, которые установщик MCP/скилла слил в корень репозитория
  (`package.json`/`package-lock.json`/`node_modules` с `shadcn-vue`), **удалены** —
  всё фронтовое живёт только в `admin-front`.
- **Полинг списка кампаний** (`CampaignsPage.vue`): фоновый опрос `getCampaigns` каждые 3 с
  (интервал `POLL_INTERVAL = 3000`, как на детальной странице). Опрашиваем **только пока есть
  хотя бы одна кампания в статусе `in_progress`** (хелпер `hasInProgress`); для `new`, завершённых
  (`done`/`done_with_errors`/`error`) и пустого списка опрос **не запускается/останавливается**
  (функция `syncPolling` стартует/останавливает таймер по этому условию). Защита `pollInFlight`
  от перекрывающихся запросов; `onUnmounted` снимает таймер. Скелетоны таблицы (`isInitialLoading`)
  показываются только при первой загрузке, фоновые тики обновляют данные «тихо», без мигания
  скелетонами.
- `.vscode/` и `node_modules/` уже в корневом `.gitignore` (покрывают и этот каталог).

## Фронтенд — линтинг и стиль (admin-front)
- **ESLint настроен** (flat config `admin-front/eslint.config.js`; скрипты `npm run lint` /
  `lint:fix`). Плагины: `@eslint/js`, `@stylistic/eslint-plugin`, `eslint-plugin-vue`,
  `eslint-plugin-import-x` (резолвер алиаса `@`→`src` с расширениями `.ts/.tsx/.jsx`),
  `typescript-eslint` (парсер TS в `<script setup lang="ts">` блоках `.vue`),
  `eslint-plugin-better-tailwindcss`.
- `src/components/ui/**` **игнорируется ESLint** — сгенерированный shadcn-код не правим (CLI
  перезаписывает).
- **better-tailwindcss** требует `settings['better-tailwindcss'].entryPoint` → `src/style.css`
  (Tailwind v4; иначе «no tailwind css entry point» и неверный перенос классов). Правила:
  `enforce-consistent-line-wrapping` (printWidth 120, `vueConvertToBinding:false`),
  `no-duplicate-classes`, `no-conflicting-classes`.
- `vue/padding-line-between-tags` задаётся через `prev`/`next` (НЕ `tags`/`prepend` — удалены в
  новых версиях `eslint-plugin-vue`).
- **components.json**: поле `$schema` намеренно убрано (схема не используется вообще), чтобы не
  было варнинга VS Code про untrusted remote schema. `defineConfig` для shadcn-vue не существует —
  CLI читает только `components.json`.
- **Стиль длинных Tailwind-классов**: группировать внутри `cn()` по смыслу; повторяющиеся куски
  выносить в `@utility` (в `style.css`), а не через `@apply`; состояние родителя — в CSS-переменную.
  Пример: в `AppHeader.vue` удалён мёртвый no-op
  `group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)` (дублировал базовую
  высоту) и добавлен `@utility transition-size`.
- **Стили наших компонентов → CSS Modules**: все Tailwind-утилиты в проектных `.vue`-файлах
  (вне `src/components/ui/**`) переписаны на `<style module>` с осмысленными классами
  (`<div :class="$style.campaignsTable">` и т.п.). Семантические токены shadcn берутся из
  CSS-переменных (`color: var(--foreground)`, `var(--muted-foreground)`, `var(--destructive)`,
  `var(--border)`, `var(--radius-md)` и т.п.); цвета статусов-бейджей (синий/жёлтый/зелёный/красный)
  заданы литералами с тёмной веткой через `:global(.dark) .statusX`. `!important` НЕ используется:
  в бандле стили SFC-модуля инжектятся **после** глобального Tailwind, поэтому при равной
  специфичности (0,1,0) наш класс перебивает базовый вариант `Badge` (`bg-primary`) по порядку в
  каскаде; тёмная ветка имеет специфичность 0,2,0 и побеждает в любом случае. Tailwind
  по-прежнему нужен для сгенерированных shadcn-компонентов — не убирать.
- **Правило именования классов**: класс на корневом тэге компонента называется так же, как сам
  компонент (в camelCase): `CampaignsTable.vue` → `.campaignsTable`, `CampaignDetailsPage.vue` →
  `.campaignDetailsPage`, `AppHeader.vue` → `.appHeader` и т.д. Внутренние классы (`.headerRow`,
  `.infoCard`, `.statusNew`, `.skId` и пр.) именуются по смыслу. `SidebarMenu.vue` исключение: его
  корень — `<SidebarGroup>` без класса, а `:class="$style.menu"` висит на вложенном `<SidebarMenu>`.

## Прогресс реализации (по шагам)
- [x] **Шаг 1** — каркас: `app/__init__.py`, `app/core/*` (config, constants, logging);
  Pipenv-конфиг (`Pipfile`, `Pipfile.lock`), `requirements.txt` удалён.
- [x] **Шаг 2** — `app/db/` (base, session, models) + `app/__main__.py`. Таблицы
  `campaigns` / `recipients` / `attachments` создаются через `create_all`.
- [x] **Шаг 3** — `app/schemas/` (campaign.py, recipient.py): CreateCampaign/Read,
  RecipientCreate/Read, RecipientsBulk, AttachmentRead, MessageOut.
- [x] **Шаг 4** — `app/services/mail_sender.py`: класс `MailSender` (connect, build,
  retry 2/4/8 с, is_temporary). Не зависит от БД.
- [x] **Шаг 5** — `app/services/recipient_service.py` + `app/services/campaign_service.py`
  (валидация email/дубликаты/файлы/размер, CRUD, импорт CSV из `import_csv.py`).
- [x] **Шаг 6** — `app/services/worker.py` (фоновый поток) + `lifespan` в `app/main.py`.
- [x] **Шаг 7** — `app/api/` роутеры (campaigns, recipients, attachments, health) +
  сборка `app/main.py`.
- [x] **Шаг 8** — `Makefile`, `.env.example` (SMTP_*, DATABASE_URL, ATTACHMENTS_DIR).
- [x] **Шаг 9** — обновить `README.md` под запуск `python -m app` / `make dev` и эндпоинты.

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
