"""Celery beat scheduler configuration."""

import os
from datetime import timedelta

from celery import Celery

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

app = Celery(
    "scheduler",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["workers.worker"],
)

app.conf.beat_schedule = {
    "record-heartbeat": {
        "task": "workers.worker.record_heartbeat",
        "schedule": timedelta(seconds=30),
    }
}
app.conf.timezone = "UTC"
