"""Configuration Celery/Beat pour la mise à jour quotidienne des embeddings."""

from celery.schedules import crontab

broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/0"
timezone = "America/Montreal"

beat_schedule = {
    "update-daily-embeddings": {
        "task": "tasks.update_all_embeddings",
        "schedule": crontab(hour=2, minute=30),
    },
}
