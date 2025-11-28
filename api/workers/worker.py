"""Celery worker configuration and tasks."""

import logging
import os
from datetime import datetime

from celery import Celery
from celery.utils.log import get_task_logger

from connectors.openai import OpenAIClient
from connectors.supabase import SupabaseClient

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_task_logger(__name__)

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery_app = Celery(
    "worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["workers.worker"],
)


@celery_app.task(name="workers.worker.generate_response")
def generate_response(prompt: str) -> str:
    """Generate text via OpenAI and persist to Supabase."""

    logger.info("Generating response for prompt: %s", prompt)
    openai_client = OpenAIClient()
    supabase_client = SupabaseClient()

    response_text = openai_client.generate_text(prompt)
    supabase_client.log_message(
        {
            "prompt": prompt,
            "response": response_text,
            "created_at": datetime.utcnow().isoformat(),
        }
    )
    logger.info("Generated response logged to Supabase")
    return response_text


@celery_app.task(name="workers.worker.record_heartbeat")
def record_heartbeat() -> str:
    """Simple heartbeat task used by the scheduler to verify connectivity."""

    message = f"Heartbeat at {datetime.utcnow().isoformat()}"
    logger.info(message)
    return message
