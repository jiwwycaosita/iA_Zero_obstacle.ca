import os
from datetime import datetime

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "celery_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)


@celery_app.task(name="workers.celery_worker.ping")
def ping() -> dict:
    """Simple task to verify the worker is alive."""
    return {"message": "pong", "timestamp": datetime.utcnow().isoformat()}


@celery_app.task(name="workers.celery_worker.add")
def add(first_number: int, second_number: int) -> int:
    """Add two integers asynchronously."""
    return first_number + second_number
