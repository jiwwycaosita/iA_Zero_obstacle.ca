"""FastAPI application entrypoint."""

import os

from celery.result import AsyncResult
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from workers.worker import celery_app

load_dotenv()

app = FastAPI(title="AI Orchestrator", version="0.1.0")


class PromptRequest(BaseModel):
    prompt: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/generate")
def generate(prompt: PromptRequest) -> dict[str, str]:
    task = celery_app.send_task("workers.worker.generate_response", args=[prompt.prompt])
    return {"task_id": task.id}


@app.get("/tasks/{task_id}")
def get_task_status(task_id: str) -> dict[str, str | None]:
    result = AsyncResult(task_id, app=celery_app)

    if result.failed():
        raise HTTPException(status_code=500, detail=str(result.result))

    response: dict[str, str | None] = {
        "task_id": task_id,
        "status": result.status,
        "result": None,
    }
    if result.successful():
        response["result"] = result.get()
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.getenv("FASTAPI_HOST", "0.0.0.0"),
        port=int(os.getenv("FASTAPI_PORT", "8000")),
        reload=True,
    )
