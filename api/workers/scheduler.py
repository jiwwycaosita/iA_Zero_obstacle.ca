import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "celery_scheduler",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["api.workers.celery_worker"],
)

celery_app.conf.beat_schedule = {
    "ping-every-minute": {
        "task": "api.workers.celery_worker.ping",
        "schedule": crontab(minute="*/1"),
    }
}

celery_app.conf.timezone = "UTC"
