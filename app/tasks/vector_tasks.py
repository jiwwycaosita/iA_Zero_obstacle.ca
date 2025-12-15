"""
Tâches Celery pour calculer et mettre à jour les embeddings dans Supabase.

Le worker lit les programmes, génère les embeddings via OpenAI et effectue un
upsert dans la table ``vector_chunks`` pour bénéficier d'un index PGVector
(IVFFlat conseillé). La colonne ``program_id`` doit être unique afin que
l'upsert fonctionne correctement.
"""

import asyncio
import os
from typing import Any, Dict, List

from celery import Celery
from supabase import Client, create_client

from app.services.embedding import get_text_embedding

celery_app = Celery("vector_tasks")
celery_app.config_from_object("app.celeryconfig")


def _get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent être définies.")
    return create_client(supabase_url, supabase_key)


@celery_app.task(name="tasks.update_all_embeddings")
def update_all_embeddings() -> None:
    """Point d'entrée Celery (synchrone)."""
    asyncio.run(_run_update_task())


async def _run_update_task() -> None:
    supabase = _get_supabase_client()
    try:
        programs_response = supabase.table("programs").select(
            "id, code, name, description, province, category"
        ).execute()
    except Exception as exc:  # pragma: no cover - dépendance réseau
        print(f"Impossible de récupérer les programmes : {exc}")
        return

    programs: List[Dict[str, Any]] = programs_response.data or []
    if not programs:
        print("Aucun programme à indexer.")
        return

    print(f"{len(programs)} programmes récupérés pour la mise à jour.")

    chunks_to_upsert: List[Dict[str, Any]] = []
    for program in programs:
        text_to_embed = (
            f"Nom: {program.get('name', '')}. "
            f"Description: {program.get('description', '')}. "
            f"Catégorie: {program.get('category', '')}. "
            f"Province: {program.get('province', 'N/A')}"
        )
        embedding = await get_text_embedding(text_to_embed)
        chunks_to_upsert.append(
            {
                "program_id": program.get("id"),
                "text": text_to_embed,
                "embedding": embedding,
            }
        )

    print(f"Upsert de {len(chunks_to_upsert)} chunks dans vector_chunks...")
    try:
        response = supabase.table("vector_chunks").upsert(
            chunks_to_upsert, on_conflict="program_id"
        ).execute()
    except Exception as exc:  # pragma: no cover - dépendance réseau
        print(f"Erreur lors de l'upsert des embeddings : {exc}")
        return

    updated_count = len(response.data or [])
    print(f"Succès : {updated_count} embeddings ont été mis à jour.")
