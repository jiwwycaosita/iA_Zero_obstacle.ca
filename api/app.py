import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api.workers.celery_worker import celery_app, add

app = FastAPI(title="Example Celery API", version="0.1.0")


class AddJobRequest(BaseModel):
    first_number: int
    second_number: int


@app.get("/")
async def health_check() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok", "service": app.title}


@app.post("/enqueue")
async def enqueue_job(job_request: AddJobRequest) -> dict:
    """Enqueue a simple addition task for the Celery worker."""
    if not os.getenv("REDIS_URL"):
        raise HTTPException(status_code=500, detail="Missing REDIS_URL configuration")

    task = add.delay(job_request.first_number, job_request.second_number)
    return {"task_id": task.id, "status": "queued"}
