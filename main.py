# main.py
# Serveur FastAPI orchestrant des agents Zero Obstacle auto-hébergeables.
# - Utilise Ollama (HTTP) pour les réponses LLM locales
# - Agents : extraction PDF, admissibilité, préremplissage, généraliste
# - Endpoints de démonstration prêts pour WordPress via le plugin fourni

import base64
import io
import json
import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

app = FastAPI(title="Zero Obstacle Agents", version="0.2.0")

# CORS large pour MVP — à restreindre au domaine WordPress ensuite.
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
    Appelle le modèle local via Ollama. Nécessite :
    - Ollama en cours d'exécution
    - modèle déjà téléchargé (ex: `ollama pull llama3.1`)
    """
    url = f"{OLLAMA_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Erreur Ollama: {exc}") from exc
    return data.get("response", "").strip()


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
<<<TEXTE_FORMULAIRE>>>
{raw_text[:6000]}
<<<FIN_TEXTE_FORMULAIRE>>>

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
    response = await call_ollama(prompt)
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        data = {
            "fields": [],
            "raw_response": response,
        }
    return data


async def agent_admissibility(
    user_profile: Dict[str, Any], program_rules: List[ProgramRule]
) -> Dict[str, Any]:
    """
    Applique STRICTEMENT les règles fournies. Pas de création de nouvelles règles.
    Les règles sont purement techniques, pas juridiques.
    """
    rules_json = json.dumps([r.dict() for r in program_rules], ensure_ascii=False)
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

    response = await call_ollama(prompt)
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        data = {
            "eligible": False,
            "failed_rules": [],
            "details": f"Réponse non JSON du modèle : {response}",
        }
    return data


async def agent_prefill_form(
    user_profile: Dict[str, Any], fields_schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Propose un préremplissage strictement basé sur les données du profil.
    Ne devine pas des informations absentes.
    """
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
    response = await call_ollama(prompt)
    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        data = {
            "values": {},
            "details": f"Réponse non JSON du modèle : {response}",
        }
    return data


# =========================
#         Endpoints
# =========================


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "model": OLLAMA_MODEL}


@app.post("/agent/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(req: OrchestrationRequest) -> OrchestrationResponse:
    """
    Endpoint général appelé par WordPress.
    Selon task, route vers l'agent approprié.
    """
    if req.task == "pdf_extraction":
        if not req.pdf_base64:
            raise HTTPException(status_code=400, detail="pdf_base64 manquant")
        try:
            pdf_bytes = base64.b64decode(req.pdf_base64)
        except Exception as exc:  # pragma: no cover - parsing safety
            raise HTTPException(status_code=400, detail="pdf_base64 invalide") from exc

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
            raise HTTPException(
                status_code=400,
                detail="user_profile et program_rules sont requis",
            )
        result = await agent_admissibility(req.user_profile, req.program_rules)
        return OrchestrationResponse(task=req.task, result=result)

    if req.task == "prefill":
        if not req.user_profile or not req.text:
            raise HTTPException(
                status_code=400,
                detail="user_profile et text (schéma) sont requis",
            )
        try:
            fields_schema = json.loads(req.text)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400, detail="text doit contenir un JSON de schéma de champs"
            ) from exc
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


# =========================
#           Démos
# =========================


@app.get("/demo/admissibility")
async def demo_admissibility() -> Dict[str, Any]:
    """Démo purement technique (non juridique)."""
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
    return {
        "profile": demo_profile,
        "rules": [r.dict() for r in demo_rules],
        "result": result,
    }


@app.get("/demo/prefill")
async def demo_prefill() -> Dict[str, Any]:
    """Démo de préremplissage sur un schéma fictif."""
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
    return {
        "profile": demo_profile,
        "fields_schema": fields_schema,
        "result": result,
    }


@app.get("/demo/pdf")
async def demo_pdf_instructions() -> Dict[str, str]:
    """
    Rappelle comment utiliser l'endpoint pdf_extraction côté client.
    """
    return {
        "info": "Encodez un PDF en base64 et envoyez-le via POST /agent/orchestrate avec task=pdf_extraction",
        "example_fields": "pdf_base64, task",
    }


# Point d'entrée de développement local : uvicorn main:app --host 0.0.0.0 --port 8080
