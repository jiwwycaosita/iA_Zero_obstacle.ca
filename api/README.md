# API Celery Example

Cette application est un **exemple** d'API FastAPI avec intégration Celery pour traitement asynchrone.

## Structure

- `app.py` : API FastAPI principale avec endpoint pour enqueuer des tâches
- `workers/celery_worker.py` : Worker Celery avec tâches asynchrones
- `workers/scheduler.py` : Scheduler Celery pour tâches planifiées
- `connectors/openai_connector.py` : Connecteur OpenAI
- `connectors/supabase_connector.py` : Connecteur Supabase

## Démarrage avec Docker

```bash
# Depuis la racine du projet
docker-compose up
```

Cela démarre :
- L'API sur le port 8000
- Le worker Celery
- Le scheduler Celery
- Redis (broker et backend)

## Variables d'environnement

Voir `.env.example` dans la racine du projet. Les variables nécessaires sont :

```
REDIS_URL=redis://redis:6379/0
OPENAI_API_KEY=your-openai-api-key
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
```

## Test de l'API

```bash
# Health check
curl http://localhost:8000/

# Enqueue une tâche d'addition
curl -X POST http://localhost:8000/enqueue \
  -H "Content-Type: application/json" \
  -d '{"first_number": 5, "second_number": 3}'
```

## Note importante

Cette application est **distincte** de l'application principale Zero Obstacle (`main.py` à la racine).
Elle sert d'exemple pour l'intégration de Celery, Redis, OpenAI et Supabase.
