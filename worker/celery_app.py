from celery import Celery
from celery.schedules import crontab
from app.config import REDIS_URL

celery_app = Celery("news_worker", broker=REDIS_URL, backend=REDIS_URL)
celery_app.conf.imports = ["worker.tasks"]

celery_app.conf.beat_schedule = {
    "fetch-news-every-30-min": {
        "task": "worker.tasks.fetch_news",
        "schedule": crontab(minute="*/30"),
    },
}
celery_app.conf.timezone = "Europe/Moscow"
