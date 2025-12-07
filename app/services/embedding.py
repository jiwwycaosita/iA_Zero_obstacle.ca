"""
Service utilitaire pour générer des embeddings textuels.

Ce module utilise l'API OpenAI en mode asynchrone. Il est conçu pour être
appelé depuis des workers Celery ou des routes FastAPI afin de préparer des
vecteurs destinés à une base PGVector (index IVFFlat recommandé).
"""

import os
from typing import List

import openai
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("La clé API OpenAI 'OPENAI_API_KEY' n'est pas définie.")

openai.api_key = OPENAI_API_KEY
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSION = 1536  # Dimension du modèle text-embedding-3-small


async def get_text_embedding(text: str) -> List[float]:
    """Retourne le vecteur d'embedding pour un texte.

    - Utilise l'API OpenAI en mode asynchrone (``acreate``) pour ne pas bloquer
      l'évent loop des appels réseau.
    - Retourne un vecteur nul si le texte est vide ou en cas d'erreur afin de
      ne pas interrompre un traitement batch.
    """
    if not text or not text.strip():
        return [0.0] * EMBEDDING_DIMENSION

    try:
        response = await openai.Embedding.acreate(input=text, model=EMBEDDING_MODEL)
        embedding = response["data"][0]["embedding"]
        return embedding
    except Exception as exc:  # pragma: no cover - tolérance aux erreurs réseau
        print(
            f"Erreur lors de la génération de l'embedding pour le texte "
            f"'{text[:50]}...': {exc}"
        )
        return [0.0] * EMBEDDING_DIMENSION
