# main.py
#
# Serveur d'agents Zero Obstacle
# - API FastAPI
# - Intégration Ollama
# - Agents : orchestrateur, PDF, admissibilité, préremplissage
#
# Dépendances :
#   pip install fastapi uvicorn[standard] httpx pydantic pypdf python-dotenv

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


class TowingCalculationRequest(BaseModel):
    vehicle_type: str  # "car", "truck", "motorcycle", "suv"
    distance_km: float
    location: str  # Province/Territory code
    service_type: str  # "standard", "urgent", "accident"
    additional_services: Optional[List[str]] = None  # "winch", "flatbed", etc.


class TaxOptimizationRequest(BaseModel):
    province: str
    income: float
    filing_status: str  # "single", "married", "common_law"
    dependents: int
    business_income: Optional[float] = None
    investment_income: Optional[float] = None
    rrsp_contribution: Optional[float] = None
    rdsp_contribution: Optional[float] = None
    other_credits: Optional[Dict[str, Any]] = None
    years_to_analyze: Optional[List[int]] = None  # Past, present, future years


class OrchestrationRequest(BaseModel):
    task: str  # "pdf_extraction", "admissibility", "prefill", "general", "towing_calculator", "tax_optimization"
    text: Optional[str] = None
    pdf_base64: Optional[str] = None
    user_profile: Optional[Dict[str, Any]] = None
    program_rules: Optional[List[ProgramRule]] = None
    towing_data: Optional[TowingCalculationRequest] = None
    tax_data: Optional[TaxOptimizationRequest] = None


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


async def agent_towing_calculator(towing_data: TowingCalculationRequest) -> Dict[str, Any]:
    """
    Calcule les frais de remorquage selon le type de véhicule, la distance,
    la localisation et les services additionnels.
    Utilise des tarifs de base réalistes pour le Canada.
    """
    import json

    towing_json = json.dumps(towing_data.dict(), ensure_ascii=False)

    prompt = f"""
Tu es un expert en calcul de frais de remorquage au Canada.

Données de remorquage :
{towing_json}

Tâche :
1. Calcule les frais de base selon :
   - Type de véhicule (voiture: 100-150$, camion: 150-250$, moto: 80-120$, VUS: 120-180$)
   - Distance (tarif de base + environ 3-5$/km)
   - Province/territoire (variations régionales)
   - Type de service (standard, urgent +50%, accident +75%)
   - Services additionnels (treuil: +50-100$, plateforme: +75-150$)

2. Calcule les taxes applicables selon la province (TPS/TVQ/TVH)

3. Fournis une estimation détaillée avec:
   - Frais de base
   - Frais de distance
   - Suppléments
   - Sous-total
   - Taxes
   - Total estimé
   - Plage de prix (min-max)
   - Recommandations pour économiser

Retourne UNIQUEMENT un JSON valide de la forme :
{{
  "base_fee": <nombre>,
  "distance_fee": <nombre>,
  "service_surcharge": <nombre>,
  "additional_fees": {{"service_name": <nombre>}},
  "subtotal": <nombre>,
  "taxes": {{"type": "rate", "amount": <nombre>}},
  "total_estimated": <nombre>,
  "price_range": {{"min": <nombre>, "max": <nombre>}},
  "recommendations": ["..."],
  "reliability_score": <0-100>,
  "disclaimer": "..."
}}
"""

    llm_response = await call_ollama(prompt)
    try:
        calculation = json.loads(llm_response)
    except Exception:
        calculation = {
            "error": "Impossible de calculer les frais",
            "raw_response": llm_response,
        }
    return calculation


async def agent_tax_optimization(tax_data: TaxOptimizationRequest) -> Dict[str, Any]:
    """
    Agent d'optimisation fiscale et de recherche de crédits/subventions.
    Analyse complète des programmes gouvernementaux fédéraux et provinciaux.
    Optimise les stratégies fiscales pour maximiser les économies.
    """
    import json

    tax_json = json.dumps(tax_data.dict(), ensure_ascii=False)

    prompt = f"""
Tu es un expert fiscal canadien spécialisé dans l'optimisation fiscale et les programmes gouvernementaux.

Données du contribuable :
{tax_json}

Tâche COMPLÈTE :

1. ANALYSE DES PROGRAMMES GOUVERNEMENTAUX :
   - Identifie TOUS les programmes fédéraux applicables (Allocation canadienne pour enfants, Crédit TPS/TVH, etc.)
   - Identifie TOUS les programmes provinciaux/territoriaux applicables
   - Calcule les montants estimés pour chaque programme
   - Indique le taux de fiabilité basé sur les informations fournies

2. CALCUL D'IMPÔT DÉTAILLÉ :
   - Revenu imposable total (emploi + entreprise + investissements)
   - Taux d'imposition marginal fédéral et provincial
   - Taux d'imposition effectif
   - Impôt fédéral et provincial
   - Crédits d'impôt applicables (de base, conjoint, personnes à charge, etc.)

3. OPTIMISATION RRSP/REEI :
   - Contribution optimale au RRSP pour réduire l'impôt
   - Économies d'impôt par tranche de contribution
   - Contribution au REEI si applicable
   - Subventions et bons du gouvernement

4. STRATÉGIES D'OPTIMISATION :
   - Fractionnement du revenu (si applicable)
   - Déductions et crédits manqués
   - Optimisation des placements (compte enregistré vs non-enregistré)
   - Stratégies pour années futures

5. ANALYSE COMPARATIVE :
   - Scénario actuel
   - Scénario optimisé
   - Gains/pertes pour chaque option
   - Impact sur années passées (si applicable pour révision)
   - Projections futures (3-5 ans)

6. CONTESTATION ET RÉVISION :
   - Décisions administratives possiblement contestables
   - Montants d'impôt à réviser
   - Délais et procédures

IMPORTANT :
- Fournis un score de fiabilité (0-100%) basé sur la complétude des informations
- Indique clairement quelles informations manquantes amélioreraient la précision
- Toutes estimations sont basées sur les lois fiscales canadiennes en vigueur
- L'utilisateur est responsable de fournir des informations complètes et exactes

Retourne UNIQUEMENT un JSON valide de la forme :
{{
  "reliability_score": <0-100>,
  "missing_information": ["..."],
  "federal_programs": [
    {{
      "name": "...",
      "eligibility": true/false,
      "estimated_amount": <nombre>,
      "requirements": ["..."],
      "application_link": "..."
    }}
  ],
  "provincial_programs": [...],
  "tax_calculation": {{
    "total_income": <nombre>,
    "taxable_income": <nombre>,
    "federal_tax": <nombre>,
    "provincial_tax": <nombre>,
    "total_tax": <nombre>,
    "marginal_rate": <nombre>,
    "effective_rate": <nombre>,
    "credits": {{"credit_name": <nombre>}}
  }},
  "rrsp_optimization": {{
    "current_contribution": <nombre>,
    "optimal_contribution": <nombre>,
    "tax_savings": <nombre>,
    "contribution_room": <nombre>
  }},
  "rdsp_analysis": {{
    "eligible": true/false,
    "optimal_contribution": <nombre>,
    "government_grants": <nombre>,
    "government_bonds": <nombre>
  }},
  "optimization_strategies": [
    {{
      "strategy": "...",
      "current_situation": "...",
      "optimized_situation": "...",
      "estimated_savings": <nombre>,
      "complexity": "low/medium/high",
      "timeline": "immediate/short-term/long-term"
    }}
  ],
  "comparative_analysis": {{
    "current_scenario": {{
      "total_tax": <nombre>,
      "net_income": <nombre>,
      "government_benefits": <nombre>
    }},
    "optimized_scenario": {{
      "total_tax": <nombre>,
      "net_income": <nombre>,
      "government_benefits": <nombre>
    }},
    "total_improvement": <nombre>
  }},
  "contestation_opportunities": [
    {{
      "type": "...",
      "description": "...",
      "potential_recovery": <nombre>,
      "deadline": "...",
      "complexity": "low/medium/high"
    }}
  ],
  "future_projections": {{
    "year_1": {{"tax": <nombre>, "benefits": <nombre>}},
    "year_3": {{"tax": <nombre>, "benefits": <nombre>}},
    "year_5": {{"tax": <nombre>, "benefits": <nombre>}}
  }},
  "recommendations": ["..."],
  "disclaimer": "Cette analyse est basée sur les informations fournies et les lois fiscales actuelles. Consultez un fiscaliste pour des conseils personnalisés. L'utilisateur est responsable de l'exactitude des informations fournies."
}}
"""

    llm_response = await call_ollama(prompt)
    try:
        optimization = json.loads(llm_response)
    except Exception:
        optimization = {
            "error": "Impossible de compléter l'analyse fiscale",
            "raw_response": llm_response[:500],
            "reliability_score": 0,
            "disclaimer": "Erreur de traitement. Veuillez réessayer ou consulter un professionnel.",
        }
    return optimization


# =========================
#         Endpoints
# =========================


@app.get("/health")
async def health():
    return {"status": "ok", "model": OLLAMA_MODEL}


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

    if request.task == "towing_calculator":
        if not request.towing_data:
            raise HTTPException(status_code=400, detail="towing_data manquant pour task=towing_calculator")
        result = await agent_towing_calculator(request.towing_data)
        return OrchestrationResponse(task=request.task, result=result)

    if request.task == "tax_optimization":
        if not request.tax_data:
            raise HTTPException(status_code=400, detail="tax_data manquant pour task=tax_optimization")
        result = await agent_tax_optimization(request.tax_data)
        return OrchestrationResponse(task=request.task, result=result)

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


@app.get("/demo/towing")
async def demo_towing():
    """
    Démo du calculateur de remorquage.
    """
    demo_towing = TowingCalculationRequest(
        vehicle_type="car",
        distance_km=25.5,
        location="QC",
        service_type="standard",
        additional_services=["winch"],
    )
    result = await agent_towing_calculator(demo_towing)
    return {"towing_data": demo_towing.dict(), "result": result}


@app.get("/demo/tax_optimization")
async def demo_tax_optimization():
    """
    Démo de l'optimisation fiscale et recherche de programmes.
    """
    demo_tax = TaxOptimizationRequest(
        province="QC",
        income=65000,
        filing_status="married",
        dependents=2,
        business_income=0,
        investment_income=2000,
        rrsp_contribution=5000,
        rdsp_contribution=0,
        years_to_analyze=[2023, 2024, 2025],
    )
    result = await agent_tax_optimization(demo_tax)
    return {"tax_data": demo_tax.dict(), "result": result}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
