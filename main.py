"""
Zero Obstacle Agents - FastAPI server with orchestrated agents.
This MVP is fully self-hostable and designed to run locally with Ollama.
"""
import os
import base64
import io
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from dotenv import load_dotenv
from pydantic import BaseModel
from pypdf import PdfReader

from app.admissibility_core import evaluate_rules

# Load environment variables from .env if present
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

app = FastAPI(title="Zero Obstacle Agents", version="0.1.0")

# CORS configuration (allow all origins by default for MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


async def call_ollama(prompt: str) -> str:
    """
    Call the local model through the Ollama HTTP API.
    Requires Ollama to be running and the chosen model pulled in advance.
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
        data = response.json()
    return data.get("response", "").strip()


def agent_extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extract raw text from a PDF using pypdf.
    This agent performs no legal interpretation; it simply extracts text.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text_chunks = []
    for page in reader.pages:
        try:
            text_chunks.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(text_chunks)


async def agent_structure_pdf_form_fields(raw_text: str) -> Dict[str, Any]:
    """
    Ask the LLM to transform raw form text into a structured list of fields (MVP).
    """
    prompt = f"""
Tu es un assistant chargé de structurer des formulaires administratifs.

Texte brut du formulaire (extraits PDF) :
---
{raw_text[:6000]}
---

Tâche :
1. Identifie les champs du formulaire (ex: nom, prénom, NAS, adresse, etc.).
2. Pour chaque champ, retourne un objet JSON :
   - "name" : nom machine (en_snake_case)
   - "label" : libellé affiché
   - "type" : "string", "date", "number", "boolean" ou "select"
   - "required" : true/false
   - "help_text" : courte explication

3. Retourne UNIQUEMENT un objet JSON valide :
{
  "fields": [ ... ]
}
"""
    response = await call_ollama(prompt)
    import json

    try:
        data = json.loads(response)
    except Exception:
        data = {
            "fields": [],
            "raw_response": response,
        }
    return data


async def agent_admissibility(user_profile: Dict[str, Any], program_rules: List[ProgramRule]) -> Dict[str, Any]:
    """
    Apply ONLY the supplied rules without creating new conditions.

    Evaluation is deterministic and does not rely on the LLM to avoid hallucinated
    logic. Supported operators: ==, =, eq, !=, neq, >, >=, <, <=, in, not_in,
    exists, not_exists. Numerical comparisons require the user value to be a
    number; otherwise the rule fails.
    """
    rule_dicts = [rule.dict() for rule in program_rules]
    return evaluate_rules(user_profile, rule_dicts)


async def agent_prefill_form(user_profile: Dict[str, Any], fields_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Propose strict form prefilling using only profile data.
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
{
  "values": {
    "<field_name>": <valeur_ou_null>
  }
}
"""
    response = await call_ollama(prompt)
    try:
        data = json.loads(response)
    except Exception:
        data = {
            "values": {},
            "details": f"Réponse non JSON du modèle : {response}",
        }
    return data


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok", "model": OLLAMA_MODEL}


@app.post("/agent/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(req: OrchestrationRequest) -> OrchestrationResponse:
    if req.task == "pdf_extraction":
        if not req.pdf_base64:
            raise HTTPException(status_code=400, detail="pdf_base64 manquant")
        try:
            pdf_bytes = base64.b64decode(req.pdf_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="pdf_base64 invalide")

        raw_text = agent_extract_pdf_text(pdf_bytes)
        structured = await agent_structure_pdf_form_fields(raw_text)
        return OrchestrationResponse(
            task=req.task,
            result={
                "raw_text_preview": raw_text[:2000],
                "structured": structured,
            },
        )

    if req.task == "admissibility":
        if not req.user_profile or not req.program_rules:
            raise HTTPException(status_code=400, detail="user_profile et program_rules sont requis")
        result = await agent_admissibility(req.user_profile, req.program_rules)
        return OrchestrationResponse(task=req.task, result=result)

    if req.task == "prefill":
        if not req.user_profile or not req.text:
            raise HTTPException(status_code=400, detail="user_profile et text (schéma) sont requis")
        import json

        try:
            fields_schema = json.loads(req.text)
        except Exception:
            raise HTTPException(status_code=400, detail="text doit contenir un JSON de schéma de champs")
        result = await agent_prefill_form(req.user_profile, fields_schema)
        return OrchestrationResponse(task=req.task, result=result)

    if req.task == "general":
        if not req.text:
            raise HTTPException(status_code=400, detail="text manquant pour task=general")
        prompt = f"""
Tu es un assistant Zero Obstacle.
Réponds de façon structurée, en expliquant clairement les étapes administratives,
sans inventer de lois ni de droits. Si une information n'est pas disponible, dis-le.
Question :
{req.text}
"""
        response = await call_ollama(prompt)
        return OrchestrationResponse(task=req.task, result={"answer": response})

    raise HTTPException(status_code=400, detail=f"Task inconnue: {req.task}")


@app.get("/demo/admissibility")
async def demo_admissibility() -> Dict[str, Any]:
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
async def demo_prefill() -> Dict[str, Any]:
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
