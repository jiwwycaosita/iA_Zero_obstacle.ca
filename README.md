# iA_GPT_Zero_obstacle - Plateforme Unifiée

Plateforme MVP d'orchestration d'agents auto-hébergeables pour le projet « Zero Obstacle ».

## Architecture Unifiée

Cette plateforme intègre :
- **Agents Zero Obstacle** : orchestrateur, extraction PDF, admissibilité, préremplissage avec Ollama
- **Celery Workers** : traitement asynchrone des tâches avec Redis
- **Connecteurs** : OpenAI et Supabase pour intégrations externes
- **Plugin WordPress** : interface utilisateur pour l'accès aux agents

## Contenu du dépôt

- `main.py` : serveur FastAPI unifié avec tous les agents et endpoints Celery
- `workers/` : workers Celery et scheduler pour tâches asynchrones
- `connectors/` : connecteurs OpenAI et Supabase
- `wordpress-plugin/zero-obstacle-agent/` : plugin WordPress pour relayer les questions vers l'orchestrateur
- `install_zero_obstacle.bat` / `start_zero_obstacle.bat` : scripts Windows pour installer et démarrer le serveur
- `test_api.py` : tests manuels simples pour vérifier l'API
- `docker-compose.yml` : orchestration Docker pour l'ensemble de la plateforme

## Prérequis

- Python 3.10+ sur la machine qui héberge l'API
- Ollama en cours d'exécution avec un modèle disponible (par défaut `llama3.1`)
- Redis pour Celery (fourni via Docker ou local)
- Optionnel : Docker et Docker Compose pour déploiement conteneurisé
- Accès réseau entre WordPress (PlanetHoster) et l'API (port 8000/8080)

## Mise en route rapide

### Option 1 : Installation Windows locale

1. **Installer l'API sur Windows**
   ```bat
   install_zero_obstacle.bat
   ```
2. **Démarrer le serveur**
   ```bat
   start_zero_obstacle.bat
   ```
3. **Vérifier la disponibilité**
   ```bash
   python test_api.py
   ```

### Option 2 : Déploiement avec Docker

1. **Créer un fichier .env**
   ```bash
   cp .env.example .env
   # Modifier .env avec vos configurations
   ```

2. **Lancer tous les services**
   ```bash
   docker-compose up -d
   ```

3. **Vérifier les services**
   ```bash
   curl http://localhost:8000/health
   ```

### Installation du plugin WordPress

- Zipper le dossier `wordpress-plugin/zero-obstacle-agent` puis téléverser-le via l'interface WP
- Configurer l'URL de l'API dans « Réglages → Zero Obstacle Agent » (ex. `http://TON_PC:8080` ou `http://votre-serveur:8000`)
- Ajouter le shortcode `[zero_obstacle_form]` dans une page ou un article

## Endpoints clés

### Endpoints de santé et monitoring
- `GET /health` : vérifie que le serveur répond et retourne les informations de configuration

### Agents Zero Obstacle
- `POST /agent/orchestrate` : route les tâches `pdf_extraction`, `admissibility`, `prefill`, `general` vers les agents dédiés
- `GET /demo/admissibility` : démo d'admissibilité
- `GET /demo/prefill` : démo de préremplissage

### Celery Workers
- `POST /celery/enqueue` : enqueue une tâche d'addition asynchrone
- `GET /celery/ping` : vérifie que le worker Celery est actif

## Configuration

Toutes les variables d'environnement sont définies dans `.env.example` :

```bash
# FastAPI
PORT=8000

# Redis / Celery
REDIS_URL=redis://redis:6379/0

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Supabase
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key

# Ollama (pour agents Zero Obstacle)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

## Services Docker

La plateforme est composée de 4 services Docker :

1. **api** : API FastAPI principale (port 8000)
2. **worker** : Worker Celery pour traitement asynchrone
3. **scheduler** : Beat scheduler Celery pour tâches planifiées
4. **redis** : Broker Redis pour Celery (port 6379)

## Notes importantes

- Les règles d'admissibilité doivent être fournies explicitement dans les requêtes (`program_rules`), aucune logique juridique n'est inventée
- Le préremplissage ne devine pas d'informations absentes du profil utilisateur
- Le parsing JSON des réponses LLM est volontairement simple pour rester un MVP ; prévoir du durcissement pour la production
- Les tâches Celery nécessitent Redis en cours d'exécution
