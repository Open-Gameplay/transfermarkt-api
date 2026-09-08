# AGENTS.md

This file provides guidance to agents working with code in this repository.

## Что это

Форк [packee-dev/transfermarkt-api](https://github.com/packee-dev/transfermarkt-api) — FastAPI
обёртка над скрейпингом transfermarkt.com. От upstream отличается: модуль национальных сборных,
модуль тренеров, фикс nullable-полей. Используется скрейпером
[transfermarkt_scrapper](https://github.com/Churikov0112/transfermarkt_scrapper) как локальный
источник данных; единый канон и конвейер — [[данные-из-transfermarkt]] вики GameplayFootball.

**Актуальная картина проекта живёт в вики: `docs/wiki/index.md` — начинать оттуда.**

## Место в пайплайне данных

Сводный договор конвейера TM → GameplayFootball — вики GameplayFootball,
`../GameplayFootball/docs/wiki/пайплайн-данных.md`. Роль: самое верхнее звено ленты —
FastAPI-обёртка над живым скрейпингом transfermarkt.com. Файлов не пишет; JSON-эндпоинты
потребляет только transfermarkt_scrapper. Менять контракт эндпоинтов — синхронно с миграцией
скрейпера.

## Ядро архитектуры

- Точка входа — `app/main.py` (uvicorn: отдельно — :8000, под скрейпером — :8001, см. «Сборка /
  запуск»; slowapi-лимит). Роуты — `app/api/endpoints/`.
- **Каждый вызов эндпоинта = живой запрос к TM** (XPath-скрейпинг, `requests` + `lxml`), кэша нет.
- Слои: `endpoints` (FastAPI) → `services/` (dataclass-скрейперы, базовый `TransfermarktBase`) →
  `schemas/` (pydantic v2). `utils/xpath.py` — все XPath-константы, `utils/regex.py` — регулярки.
- Ответы — **camelCase** (alias_generator в `schemas/base.py`), null/дефолтные поля часто вырезаются
  (`response_model_exclude_none=True`). Числа («€1.2m», рост «1,85m») парсят валидаторы `base.py`.
- Ключи: TM-id строкой; сборные и тренеры — это форк-модули (см. ниже).

### Форк-модули (наши правки поверх upstream)

- **Национальные сборные** (`app/{api,services,schemas}/national_teams/`): most-valuable, search,
  profile, players. Состав сборной возвращает `shirtNumber` (добавлено). `coach_id` API не отдаёт —
  его берёт скрейпер с `/mitarbeiter/` страницы напрямую.
- **Тренеры** (`app/{api,services}/coaches/`): единственный эндпоинт без pydantic-схемы, возвращает
  сырой dict в snake_case — **выбивается из конвенции camelCase**; не менять без необходимости.
- **Ловушки форка**: `extract_from_url` должен срезать домен и ловить `AttributeError` (иначе
  канонические URL ломают парсинг); возраст в составе сборной — со второго `td.zentriert`.

## Сборка / запуск

Python 3.9+. Зависимости — `requirements.txt` (для Poetry — `pyproject.toml`). Локально лимит
выключен (`RATE_LIMITING_ENABLE=false`), на деплое — `2/3seconds` (slowapi).

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt   # Windows
# или: poetry install
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Под скрейпер api поднимается на :8001.** Соседний `transfermarkt_scrapper` берёт
`API_BASE` по умолчанию `http://127.0.0.1:8001` (переопределяется через `TM_API_BASE`). Для
zero-config связки поднимай api именно на 8001:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Либо, если api остался на 8000, задай скрейперу `TM_API_BASE=http://127.0.0.1:8000`. Отдельно
api слушает 8000 (дефолт `uvicorn.run` в `app/main.py` и Swagger ниже).

Swagger: http://127.0.0.1:8000/docs (на 8001 — http://127.0.0.1:8001/docs)

## Устройство вики

- `docs/wiki/` — **текущее состояние**, одна страница на подсистему, кросс-ссылки вида
  `[[имя-страницы]]`, каталог в `docs/wiki/index.md`. Обновляй после правки кода.
- `docs/wiki/глоссарий.md` — имена предметной области. `CONTEXT.md` в корне — только указатель.
- `log.md` (корень) — append-only хронология. Записи `## [YYYY-MM-DD] тип | описание`.

**Правило: после любого содержательного изменения обнови соответствующую страницу вики — не
создавай новый датированный документ.**

## Workflow

- Код и комментарии — на английском (в форк-коде есть русские комментарии — не распространять);
  вики и этот файл — на русском.
- Тесты: `pytest` (tests/). Линт CI: `ruff`, `black --check`, `interrogate`.
- Git: комментарии коммитов на английском.
- Три хука (.agent/hooks/ + плагин opencode в .opencode/plugins/) поддерживают контур вики.

## Working principles

## 1. Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs.

## 2. Simplicity First
Minimum code that solves the problem. Nothing speculative.

## 3. Surgical Changes
Touch only what you must. Match existing style. Remove only what YOUR changes made unused.

## 4. Goal-Driven Execution
Define success criteria. Loop until verified.