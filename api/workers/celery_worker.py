from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()
broker = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery = Celery("zoc_worker", broker=broker)


@celery.task()
def add_task(job_name: str):
    print(f"[Celery] Démarrage du job {job_name}")
    # simulation de traitement
    import time
    time.sleep(3)
    print(f"[Celery] Job {job_name} terminé")
    return {"job": job_name, "status": "done"}
