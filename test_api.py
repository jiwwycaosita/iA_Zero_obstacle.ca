"""Simple smoke tests for the Zero Obstacle Agents FastAPI server."""
import requests

BASE_URL = "http://localhost:8080"


def test_health() -> None:
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    print("HEALTH:", response.status_code, response.text)


def test_general() -> None:
    payload = {
        "task": "general",
        "text": "Explique-moi en étapes simples comment fonctionne un formulaire d'aide financière (en général).",
    }
    response = requests.post(f"{BASE_URL}/agent/orchestrate", json=payload, timeout=60)
    print("GENERAL:", response.status_code, response.text[:500])


if __name__ == "__main__":
    test_health()
    print("-----")
    test_general()
