# Runbook Opérationnel - iA Zero Obstacle

## Installation

### Prérequis
- Windows 10/11 ou Linux/macOS
- Python 3.10+
- Ollama installé et en cours d'exécution
- Docker (optionnel, pour Redis/Celery)

### Installation rapide (Windows)
```bat
install_zero_obstacle.bat
```

### Installation manuelle
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Éditer .env et générer API_KEY avec: openssl rand -hex 32
```

## Démarrage

### Mode développement
```bash
# Windows
start_zero_obstacle.bat

# Linux/macOS
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### Mode production
```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
```

### Avec Docker
```bash
docker-compose up -d
```

## Tests

### Tests unitaires
```bash
pytest tests/ -v
```

### Tests avec couverture
```bash
pytest --cov=main --cov=api --cov-report=html
```

### Smoke test API
```bash
python test_api.py
```

## Monitoring

### Health check
```bash
curl http://localhost:8080/health
```

### Metrics
```bash
curl http://localhost:8080/metrics
```

## Sécurité

### Générer une nouvelle API Key
```bash
openssl rand -hex 32
```

### Utiliser l'API Key
```bash
curl -H "X-API-Key: YOUR_KEY" http://localhost:8080/agent/orchestrate -d '{"task":"general","text":"test"}'
```

## Troubleshooting

### Ollama non disponible
- Vérifier que Ollama tourne : `ollama list`
- Vérifier OLLAMA_URL dans .env

### Erreur 401 Unauthorized
- Vérifier que X-API-Key header est présent
- Vérifier que API_KEY dans .env correspond

### Tests échouent
- Vérifier que le serveur est démarré
- Vérifier API_KEY dans environnement de test

## Logs

Les logs sont au format JSON structuré (stdout) :
```json
{"event": "request_received", "timestamp": "2025-01-15T10:30:00", "level": "info"}
```

## Backup & Recovery

### Backup des données
```bash
tar -czf backup_$(date +%Y%m%d).tar.gz data/
```

### Rollback
```bash
git checkout main
docker-compose down
docker-compose up -d
```
