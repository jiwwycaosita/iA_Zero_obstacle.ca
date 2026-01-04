# main.py
#
# Serveur d'agents Zero Obstacle - Unified Application
# - API FastAPI
# - Intégration Ollama pour agents Zero Obstacle
# - Celery pour tâches asynchrones
# - Connecteurs OpenAI et Supabase
# - Agents : orchestrateur, PDF, admissibilité, préremplissage
#
# Dépendances :
#   pip install -r requirements.txt

import base64
import io
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader

# Importer les workers Celery
try:
    from workers.celery_worker import celery_app, add, ping
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

# Charger .env si présent
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = FastAPI(title="Zero Obstacle Unified Platform", version="1.0.0")

# CORS (MVP : tout autoriser, à restreindre plus tard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
#       Modèles Pydantic
# =========================


class ProgramRule(BaseModel):
    id: str
    description: str
    field: str
    operator: str
    value: Any
    required: bool = True


class OrchestrationRequest(BaseModel):
    task: str  # "pdf_extraction", "admissibility", "prefill", "general"
    text: Optional[str] = None
    pdf_base64: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None
    program_rules: Optional[List[ProgramRule]] = None


class OrchestrationResponse(BaseModel):
    task: str
    result: Dict[str, Any]


# =========================
#       Utilitaires LLM
# =========================


async def call_ollama(prompt: str) -> str:
    """
    Appelle le modèle local via Ollama.
    Nécessite :
      - Ollama en cours d'exécution
      - modèle tiré (ollama pull ...)

    L'API utilisée est la génération simple (non streaming).
    """

    url = f"{OLLAMA_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        response_data = response.json()
    return response_data.get("response", "").strip()


# =========================
#          Agents
# =========================


def agent_extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extraction brute du texte d'un PDF avec pypdf.
    Ne fait aucune interprétation juridique : seulement du texte.
    """

    reader = PdfReader(io.BytesIO(pdf_bytes))
    text_chunks: List[str] = []
    for page in reader.pages:
        try:
            text_chunks.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(text_chunks)


async def agent_structure_pdf_form_fields(raw_text: str) -> Dict[str, Any]:
    """
    Demande au LLM de transformer un texte brut de formulaire
    en liste structurée de champs (MVP).
    """

    prompt = f"""
Tu es un assistant chargé de structurer des formulaires administratifs.

Texte brut du formulaire (extraits PDF) :
\"\"\"{raw_text[:6000]}\"\"\"  # limité pour éviter les prompts trop longs

Tâche :
1. Identifie les champs du formulaire (ex: nom, prénom, NAS, adresse, etc.).
2. Pour chaque champ, retourne un objet JSON :
   - "name" : nom machine (en_snake_case)
   - "label" : libellé affiché
   - "type" : "string", "date", "number", "boolean" ou "select"
   - "required" : true/false
   - "help_text" : courte explication

3. Retourne UNIQUEMENT un objet JSON valide :
{{
  "fields": [ ... ]
}}
"""
    llm_response = await call_ollama(prompt)
    import json

    try:
        structured_data = json.loads(llm_response)
    except Exception:
        structured_data = {
            "fields": [],
            "raw_response": llm_response,
        }
    return structured_data


async def agent_admissibility(user_profile: Dict[str, Any], program_rules: List[ProgramRule]) -> Dict[str, Any]:
    """
    Applique STRICTEMENT les règles fournies.
    Pas de création de nouvelles règles.
    Les règles sont purement techniques, pas juridiques.
    """

    import json

    rules_json = json.dumps([rule.dict() for rule in program_rules], ensure_ascii=False)
    profile_json = json.dumps(user_profile, ensure_ascii=False)

    prompt = f"""
Tu es un système de règles techniques. 
Tu DOIS appliquer UNIQUEMENT les règles fournies ci-dessous. 
Tu NE DOIS PAS inventer de nouvelles conditions.

Règles (JSON) :
{rules_json}

Profil utilisateur (JSON) :
{profile_json}

Tâche :
1. Pour chaque règle, indique si elle est satisfaite ou non.
2. Détermine :
   - "eligible": true/false (true uniquement si TOUTES les règles required=true sont satisfaites)
   - "failed_rules": liste des id des règles non satisfaites
   - "details": explication courte (sans interprétation juridique, juste technique)

Retourne un JSON strictement valide de la forme :
{{
  "eligible": true/false,
  "failed_rules": ["..."],
  "details": "..."
}}
"""

    llm_response = await call_ollama(prompt)
    try:
        eligibility_result = json.loads(llm_response)
    except Exception:
        eligibility_result = {
            "eligible": False,
            "failed_rules": [],
            "details": f"Réponse non JSON du modèle : {llm_response}",
        }
    return eligibility_result


async def agent_prefill_form(user_profile: Dict[str, Any], fields_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Propose un préremplissage strictement basé sur les données du profil.
    Ne devine pas des informations absentes.
    """

    import json

    fields_json = json.dumps(fields_schema, ensure_ascii=False)
    profile_json = json.dumps(user_profile, ensure_ascii=False)

    prompt = f"""
Tu dois préremplir un formulaire à partir d'un profil utilisateur.

Schéma des champs :
{fields_json}

Profil utilisateur :
{profile_json}

Règles :
- Tu n'inventes aucune information.
- Si une donnée n'est pas présente dans le profil, tu mets la valeur null.
- Tu respectes les types : string, number, boolean, date.

Retour attendu (JSON) :
{{
  "values": {{
    "<field_name>": <valeur_ou_null>
  }}
}}
"""
    llm_response = await call_ollama(prompt)
    try:
        prefilled_values = json.loads(llm_response)
    except Exception:
        prefilled_values = {
            "values": {},
            "details": f"Réponse non JSON du modèle : {llm_response}",
        }
    return prefilled_values


# =========================
#         Endpoints
# =========================


@app.get("/health")
async def health():
    """Health check for the entire platform."""
    return {
        "status": "ok",
        "model": OLLAMA_MODEL,
        "celery_available": CELERY_AVAILABLE,
        "redis_url": REDIS_URL if CELERY_AVAILABLE else None
    }


# =========================
# Celery Worker Endpoints
# =========================


class AddJobRequest(BaseModel):
    """Request model for adding two numbers via Celery."""
    first_number: int
    second_number: int


@app.post("/celery/enqueue")
async def enqueue_job(job_request: AddJobRequest) -> dict:
    """Enqueue a simple addition task for the Celery worker."""
    if not CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Celery is not available")

    task = add.delay(job_request.first_number, job_request.second_number)
    return {"task_id": task.id, "status": "queued"}


@app.get("/celery/ping")
async def celery_ping() -> dict:
    """Trigger a ping task to verify Celery worker is alive."""
    if not CELERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Celery is not available")
    
    task = ping.delay()
    return {"task_id": task.id, "status": "queued"}


# =========================
# Zero Obstacle Agents
# =========================


@app.post("/agent/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(request: OrchestrationRequest):
    """
    Endpoint général appelé par WordPress.
    Selon task, route vers l'agent approprié.
    """

    if request.task == "pdf_extraction":
        if not request.pdf_base64:
            raise HTTPException(status_code=400, detail="pdf_base64 manquant")
        try:
            pdf_bytes = base64.b64decode(request.pdf_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="pdf_base64 invalide")

        raw_text = agent_extract_pdf_text(pdf_bytes)
        structured = await agent_structure_pdf_form_fields(raw_text)
        return OrchestrationResponse(
            task=request.task,
            result={
                "raw_text_preview": raw_text[:2000],
                "structured": structured,
            },
        )

    if request.task == "admissibility":
        if not request.user_profile or not request.program_rules:
            raise HTTPException(status_code=400, detail="user_profile et program_rules sont requis")
        result = await agent_admissibility(request.user_profile, request.program_rules)
        return OrchestrationResponse(task=request.task, result=result)

    if request.task == "prefill":
        if not request.user_profile or not request.text:
            raise HTTPException(status_code=400, detail="user_profile et text (schéma) sont requis")
        import json

        try:
            fields_schema = json.loads(request.text)
        except Exception:
            raise HTTPException(status_code=400, detail="text doit contenir un JSON de schéma de champs")
        result = await agent_prefill_form(request.user_profile, fields_schema)
        return OrchestrationResponse(task=request.task, result=result)

    if request.task == "general":
        if not request.text:
            raise HTTPException(status_code=400, detail="text manquant pour task=general")
        prompt = f"""
Tu es un assistant Zero Obstacle.
Réponds de façon structurée, en expliquant clairement les étapes administratives,
sans inventer de lois ni de droits. Si une information n'est pas disponible, dis-le.
Question :
{request.text}
"""
        llm_response = await call_ollama(prompt)
        return OrchestrationResponse(task=request.task, result={"answer": llm_response})

    raise HTTPException(status_code=400, detail=f"Task inconnue: {request.task}")


# =========================
#           Démos
# =========================


@app.get("/demo/admissibility")
async def demo_admissibility():
    """
    Démo purement technique (non juridique).
    """

    demo_profile = {
        "province": "QC",
        "age": 35,
        "income": 25000,
        "single_parent": True,
    }
    demo_rules = [
        ProgramRule(
            id="age_min_18",
            description="Âge minimum 18 ans",
            field="age",
            operator=">=",
            value=18,
            required=True,
        ),
        ProgramRule(
            id="max_income_30000",
            description="Revenu maximal 30 000",
            field="income",
            operator="<=",
            value=30000,
            required=True,
        ),
    ]
    result = await agent_admissibility(demo_profile, demo_rules)
    return {"profile": demo_profile, "rules": [rule.dict() for rule in demo_rules], "result": result}


@app.get("/demo/prefill")
async def demo_prefill():
    """
    Démo de préremplissage sur un schéma fictif.
    """

    demo_profile = {
        "first_name": "Alex",
        "last_name": "Tremblay",
        "province": "QC",
        "email": "alex.tremblay@example.com",
    }
    fields_schema = {
        "fields": [
            {"name": "first_name", "label": "Prénom", "type": "string", "required": True},
            {"name": "last_name", "label": "Nom", "type": "string", "required": True},
            {"name": "email", "label": "Courriel", "type": "string", "required": True},
            {"name": "phone", "label": "Téléphone", "type": "string", "required": False},
        ]
    }
    result = await agent_prefill_form(demo_profile, fields_schema)
    return {"profile": demo_profile, "fields_schema": fields_schema, "result": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
