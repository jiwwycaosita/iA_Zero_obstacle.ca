"""Tests simples pour vérifier que l'API répond localement.

Usage:
    # For local Windows deployment (port 8080):
    python test_api.py
    
    # For Docker deployment (port 8000):
    API_BASE_URL=http://localhost:8000 python test_api.py
"""

import os
import requests

# Support both local Windows deployment (8080) and Docker deployment (8000)
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8080")


def test_health():
    """Test health endpoint."""
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    print("HEALTH:", response.status_code, response.text)


def test_general():
    """Test general agent endpoint."""
    payload = {
        "task": "general",
        "text": "Explique-moi en étapes simples comment fonctionne un formulaire d'aide financière (en général).",
    }
    response = requests.post(
        f"{BASE_URL}/agent/orchestrate", json=payload, timeout=60
    )
    print("GENERAL:", response.status_code, response.text[:500])


def test_celery_enqueue():
    """Test Celery enqueue endpoint (will fail if Redis is not running)."""
    try:
        payload = {
            "first_number": 5,
            "second_number": 7,
        }
        response = requests.post(
            f"{BASE_URL}/celery/enqueue", json=payload, timeout=10
        )
        print("CELERY ENQUEUE:", response.status_code, response.text)
    except Exception as e:
        print(f"CELERY ENQUEUE: Failed (Redis may not be running) - {e}")


if __name__ == "__main__":
    test_health()
    print("-----")
    test_general()
    print("-----")
    test_celery_enqueue()

