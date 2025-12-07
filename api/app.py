from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from connectors.supabase_connector import SupabaseConnector
from workers.celery_worker import add_task
from agents.profile_agent import ProfileAgent

load_dotenv()
app = FastAPI(title="Zéro Obstacle Canada – API de base")

db = SupabaseConnector(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


class JobRequest(BaseModel):
    job_name: str


@app.get("/")
def root():
    return {"status": "ok", "message": "API Zéro Obstacle prête"}


@app.post("/run_job")
def run_job(request: JobRequest):
    add_task.delay(request.job_name)
    return {"status": "queued", "job": request.job_name}


@app.post("/analyze_profile")
def analyze_profile(profile: dict):
    agent = ProfileAgent()
    result = agent.analyze_profile(profile, mode="precision")
    return result
