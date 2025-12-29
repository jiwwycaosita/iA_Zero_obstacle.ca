# main.py
# Serveur d'agents Zero Obstacle
# - API FastAPI
# - Intégration Ollama
# - Agents : orchestrateur, PDF, admissibilité, préremplissage
#
# Dépendances :
#   pip install fastapi uvicorn[standard] httpx pydantic pypdf python-dotenv

import os
import base64
import io
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
import httpx
from dotenv import load_dotenv

# Charger .env si présent (OLLAMA_URL, OLLAMA_MODEL)
load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

app = FastAPI(title="Zero Obstacle Agents", version="0.1.0")

# CORS (MVP : tout autoriser, à restreindre plus tard)
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
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    return data.get("response", "").strip()


def agent_extract_pdf_text(pdf_bytes: bytes) -> str:
    """
    Extraction brute du texte d'un PDF avec pypdf.
    Ne fait aucune interprétation juridique : seulement du texte.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text_chunks = []
    for page in reader.pages:
        try:
            text_chunks.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(text_chunks)


async def agent_structure_pdf_form_fields(raw_text: str, chunk_size: int = 4000) -> Dict[str, Any]:
    """
    Demande au LLM de transformer un texte brut de formulaire en liste structurée
    de champs (MVP).

    Pour éviter les pertes d'information sur de grands PDF, le texte est traité
    par morceaux successifs jusqu'à ingestion complète. Les champs sont
    agrégés/dédupliqués par "name".
    """
    import json

    if not raw_text:
        return {"fields": [], "chunk_results": []}

    chunks = [raw_text[i : i + chunk_size] for i in range(0, len(raw_text), chunk_size)]
    aggregated_fields: Dict[str, Dict[str, Any]] = {}
    chunk_results: List[Dict[str, Any]] = []

    for idx, chunk in enumerate(chunks):
        prompt = f"""
Tu es un assistant chargé de structurer des formulaires administratifs.

Tu traites le morceau {idx + 1}/{len(chunks)} d'un PDF. Limite-toi à ce
morceau pour éviter les répétitions, tout en gardant des clés stables.

Texte brut du formulaire (extraits PDF) :
\"\"\"{chunk}\"\"\"

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

        parsed: Dict[str, Any]
        error: str = ""
        try:
            parsed = json.loads(response)
        except Exception as exc:  # pragma: no cover - robustesse MVP
            parsed = {"fields": []}
            error = f"Réponse non JSON ({exc})"

        for field in parsed.get("fields", []):
            name = field.get("name")
            if not name:
                continue
            if name not in aggregated_fields:
                aggregated_fields[name] = field

        chunk_results.append(
            {
                "chunk_index": idx,
                "chars": len(chunk),
                "fields_found": len(parsed.get("fields", [])),
                "error": error,
            }
        )

    return {
        "fields": list(aggregated_fields.values()),
        "chunk_results": chunk_results,
    }


async def agent_admissibility(user_profile: Dict[str, Any],
                              program_rules: List[ProgramRule]) -> Dict[str, Any]:
    """
    Applique STRICTEMENT les règles fournies sans LLM pour rester déterministe.
    Pas de création de nouvelles règles.
    Les règles sont purement techniques, pas juridiques.
    """
    def evaluate_rule(rule: ProgramRule) -> Dict[str, Any]:
        if rule.field not in user_profile:
            return {
                "id": rule.id,
                "ok": False,
                "reason": f"Champ manquant: {rule.field}",
            }

        value = user_profile.get(rule.field)
        target = rule.value
        operator = rule.operator

        ok = False
        try:
            if operator == "==":
                ok = value == target
            elif operator == "!=":
                ok = value != target
            elif operator == ">=":
                ok = value >= target
            elif operator == "<=":
                ok = value <= target
            elif operator == ">":
                ok = value > target
            elif operator == "<":
                ok = value < target
            elif operator == "in":
                ok = value in target if isinstance(target, (list, tuple, set)) else value in str(target)
            elif operator == "not in":
                ok = value not in target if isinstance(target, (list, tuple, set)) else value not in str(target)
            else:
                return {
                    "id": rule.id,
                    "ok": False,
                    "reason": f"Opérateur inconnu: {operator}",
                }
        except Exception as exc:  # pragma: no cover - sécurité MVP
            return {
                "id": rule.id,
                "ok": False,
                "reason": f"Erreur d'évaluation ({exc})",
            }

        return {
            "id": rule.id,
            "ok": bool(ok),
            "reason": "",
        }

    evaluations = [evaluate_rule(rule) for rule in program_rules]
    failed_required = [
        ev["id"]
        for ev, rule in zip(evaluations, program_rules)
        if not ev["ok"] and rule.required
    ]

    eligible = len(failed_required) == 0
    return {
        "eligible": eligible,
        "failed_rules": failed_required,
        "rule_results": evaluations,
        "details": "Toutes les règles requises sont respectées." if eligible else "Certaines règles requises échouent.",
    }


async def agent_prefill_form(user_profile: Dict[str, Any],
                             fields_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Propose un préremplissage strictement basé sur les données du profil.
    Ne devine pas des informations absentes et n'utilise pas le LLM pour rester déterministe.
    """
    values: Dict[str, Any] = {}
    for field in fields_schema.get("fields", []):
        name = field.get("name")
        field_type = field.get("type", "string")
        if not name:
            continue

        raw_value = user_profile.get(name)
        if raw_value is None:
            values[name] = None
            continue

        if field_type == "number":
            try:
                values[name] = float(raw_value)
            except (TypeError, ValueError):
                values[name] = None
        elif field_type == "boolean":
            if isinstance(raw_value, bool):
                values[name] = raw_value
            elif isinstance(raw_value, str):
                values[name] = raw_value.strip().lower() in {"true", "1", "yes", "on", "y"}
            else:
                values[name] = bool(raw_value)
        else:
            values[name] = raw_value

    return {
        "values": values,
        "details": "Préremplissage basé uniquement sur les données fournies.",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "model": OLLAMA_MODEL}


@app.post("/agent/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(req: OrchestrationRequest):
    """
    Endpoint général appelé par WordPress.
    Selon task, route vers l'agent approprié.
    """
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

    elif req.task == "admissibility":
        if not req.user_profile or not req.program_rules:
            raise HTTPException(status_code=400, detail="user_profile et program_rules sont requis")
        result = await agent_admissibility(req.user_profile, req.program_rules)
        return OrchestrationResponse(task=req.task, result=result)

    elif req.task == "prefill":
        if not req.user_profile or not req.text:
            raise HTTPException(status_code=400, detail="user_profile et text (schéma) sont requis")
        import json
        try:
            fields_schema = json.loads(req.text)
        except Exception:
            raise HTTPException(status_code=400, detail="text doit contenir un JSON de schéma de champs")
        result = await agent_prefill_form(req.user_profile, fields_schema)
        return OrchestrationResponse(task=req.task, result=result)

    elif req.task == "general":
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

    else:
        raise HTTPException(status_code=400, detail=f"Task inconnue: {req.task}")


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
    return {"profile": demo_profile, "rules": [r.dict() for r in demo_rules], "result": result}


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

    uvicorn.run(app, host="0.0.0.0", port=8080)
