# Guide de Migration - Plateforme Unifiée Zero Obstacle

## Résumé des Changements

Ce document explique la migration de l'architecture multi-modules vers une plateforme unifiée.

## Avant la Migration

L'architecture précédente comportait deux applications distinctes :

1. **main.py** : Serveur FastAPI avec agents Zero Obstacle (Ollama)
2. **api/** : Application FastAPI séparée avec Celery, OpenAI, et Supabase

Cette séparation créait de la duplication et de la complexité.

## Après la Migration

Tous les modules ont été unifiés dans une seule application cohérente :

```
/
├── main.py                    # Application FastAPI unifiée
├── connectors/                # Connecteurs externes
│   ├── openai_connector.py   # Client OpenAI
│   └── supabase_connector.py # Client Supabase
├── workers/                   # Workers Celery
│   ├── celery_worker.py      # Tâches asynchrones
│   └── scheduler.py          # Planificateur
├── wordpress-plugin/          # Plugin WordPress (inchangé)
├── Dockerfile                 # Build Docker unifié
├── docker-compose.yml         # Orchestration complète
└── requirements.txt           # Toutes les dépendances
```

## Changements Détaillés

### 1. Structure des Fichiers

**Supprimé :**
- `api/` (dossier complet)
- `api/app.py`
- `api/Dockerfile`
- `api/connectors/`
- `api/workers/`
- `doc` (renommé en `.readthedocs.yml`)

**Ajouté :**
- `/connectors/` (déplacé de `api/connectors/`)
- `/workers/` (déplacé de `api/workers/`)
- `/Dockerfile` (nouveau, unifié)

**Modifié :**
- `main.py` : Intégration des endpoints Celery
- `docker-compose.yml` : Utilisation de `main:app` au lieu de `api.app:app`
- `requirements.txt` : Ajout de httpx, pypdf, requests
- `.env.example` : Ajout des variables OLLAMA_URL et OLLAMA_MODEL
- `README.md` : Documentation complète de la plateforme unifiée

### 2. Nouveaux Endpoints

Le serveur unifié expose maintenant :

**Santé et Monitoring :**
- `GET /health` - Statut de la plateforme (Ollama + Celery)

**Agents Zero Obstacle (Ollama) :**
- `POST /agent/orchestrate` - Orchestration des agents
- `GET /demo/admissibility` - Démo d'admissibilité
- `GET /demo/prefill` - Démo de préremplissage

**Celery Workers (Redis) :**
- `POST /celery/enqueue` - Enqueue une tâche asynchrone
- `GET /celery/ping` - Vérifie la santé du worker

### 3. Configuration

Toutes les variables d'environnement sont maintenant dans `.env` :

```bash
# FastAPI
PORT=8000

# Redis / Celery
REDIS_URL=redis://redis:6379/0

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

### 4. Déploiement

**Option 1 - Windows Local :**
```bat
install_zero_obstacle.bat
start_zero_obstacle.bat
```

**Option 2 - Docker Compose :**
```bash
cp .env.example .env
# Éditer .env avec vos configurations
docker-compose up -d
```

### 5. Tests

Le fichier `test_api.py` a été mis à jour pour tester :
- Endpoint `/health`
- Endpoint `/agent/orchestrate` (agents Ollama)
- Endpoint `/celery/enqueue` (workers Celery)

Lancer les tests :
```bash
python test_api.py
```

## Avantages de la Migration

1. **Simplicité** : Une seule application au lieu de deux
2. **Maintenance** : Code consolidé et plus facile à maintenir
3. **Déploiement** : Un seul Dockerfile et une configuration unifiée
4. **Performance** : Moins de overhead réseau
5. **Extensibilité** : Plus facile d'ajouter de nouvelles fonctionnalités

## Compatibilité

- ✅ Le plugin WordPress continue de fonctionner sans changement
- ✅ Les endpoints existants sont préservés
- ✅ Les agents Zero Obstacle fonctionnent comme avant
- ✅ Les workers Celery sont intégrés de manière transparente

## Migration des Imports

Si vous avez du code qui importe depuis l'ancien `api/` :

**Avant :**
```python
from api.workers.celery_worker import celery_app, add
from api.connectors.openai_connector import get_openai_client
```

**Après :**
```python
from workers.celery_worker import celery_app, add
from connectors.openai_connector import get_openai_client
```

## Notes Importantes

- Aucun module lié à EVA ou aux films n'a été ajouté (comme demandé)
- Tous les autres modules et repos ont été assemblés dans cette plateforme unifiée
- La plateforme est maintenant prête pour l'expansion future
