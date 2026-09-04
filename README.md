# Агрегатор новостей

Асинхронный агрегатор новостей на Python с использованием aiohttp, Celery и Docker. Собирает статьи из RSS-лент и предоставляет REST API для доступа к ним.

## Архитектура

```
+------------------+     +------------------+     +------------------+
|   aiohttp API    |     |  Celery Worker   |     |  Celery Beat     |
|   (app/main.py)  |     |  (fetch_news)    |     |  (расписание)    |
+--------+---------+     +--------+---------+     +--------+---------+
         |                        |                        |
         |  POST /api/fetch       |                        | каждые 30 мин
         +------------------------+------------------------+
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
            +---------------+           +---------------+
            |    Redis      |           |  PostgreSQL   |
            |  (брокер)     |           |  (данные)     |
            +---------------+           +---------------+
```

- **API** — aiohttp веб-сервер, обрабатывает HTTP-запросы
- **Worker** — Celery воркер, выполняет асинхронную загрузку RSS
- **Beat** — Celery Beat, запускает задачу fetch_news каждые 30 минут
- **Redis** — брокер сообщений для Celery
- **PostgreSQL** — хранение источников и статей

## Эндпоинты API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | /api/articles | Список статей (source_id, limit, offset, search) |
| GET | /api/articles/{id} | Детали статьи |
| GET | /api/sources | Список источников |
| POST | /api/sources | Добавить источник (name, url) |
| DELETE | /api/sources/{id} | Удалить источник |
| POST | /api/fetch | Запустить ручную загрузку новостей |

### Примеры запросов

```
GET /api/articles?limit=10&offset=0
GET /api/articles?source_id=1&search=python
POST /api/sources
Content-Type: application/json
{"name": "Хабр", "url": "https://habr.com/ru/rss/best/daily/"}
```

## Установка и запуск

### Локально

1. Создать виртуальное окружение и установить зависимости:

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Запустить PostgreSQL и Redis (через Docker или локально).

3. Скопировать `.env.example` в `.env` и при необходимости изменить настройки.

4. Запустить приложение:

```
python -m app.main
```

5. В отдельных терминалах запустить Celery worker и beat:

```
celery -A worker.celery_app worker --loglevel=info
celery -A worker.celery_app beat --loglevel=info
```

### Docker

```
docker-compose up --build
```

Сервисы:
- API: http://localhost:8080
- PostgreSQL: localhost:5432
- Redis: localhost:6379

При первом запуске автоматически создаются таблицы и добавляются источники по умолчанию (Habr, Lenta.ru, RBC Tech).
