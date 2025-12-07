import time
from celery import Celery
from datetime import datetime

celery = Celery(broker="redis://redis:6379/0")

JOBS = ["scrape_canada", "update_forms", "refresh_laws"]


while True:
    print(f"[Scheduler] Lancement du cycle {datetime.utcnow()}")
    for job in JOBS:
        celery.send_task("workers.celery_worker.add_task", args=[job])
    time.sleep(6 * 3600)  # relance toutes les 6h
