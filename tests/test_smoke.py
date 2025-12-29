import pytest
import requests
import os

BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8080")
API_KEY = os.getenv("API_KEY", "test-key")

def test_health_endpoint():
    """Test endpoint /health sans auth"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert "model" in data or "status" in data

def test_metrics_endpoint():
    """Test endpoint /metrics sans auth"""
    response = requests.get(f"{BASE_URL}/metrics")
    assert response.status_code == 200

def test_protected_endpoint_without_key():
    """Test qu'un endpoint protégé refuse sans API key"""
    response = requests.post(f"{BASE_URL}/agent/orchestrate", json={"task": "general"})
    assert response.status_code == 401

def test_protected_endpoint_with_key():
    """Test qu'un endpoint protégé accepte avec API key valide"""
    headers = {"X-API-Key": API_KEY}
    payload = {"task": "general", "text": "Test question"}
    
    response = requests.post(f"{BASE_URL}/agent/orchestrate", json=payload, headers=headers)
    # Peut être 200 ou 500 selon si Ollama est disponible, mais pas 401
    assert response.status_code != 401
