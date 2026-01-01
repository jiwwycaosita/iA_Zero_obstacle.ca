# iA_GPT_Zero_obstacle

Plateforme MVP d'orchestration d'agents auto-hébergeables pour le projet « Zero Obstacle ».

## Structure du projet

Ce dépôt contient **deux applications distinctes** :

### 1. Application principale : Zero Obstacle Agents (`main.py`)
- Serveur FastAPI avec orchestrateur et agents (extraction PDF, admissibilité, préremplissage, questions générales)
- Utilise Ollama pour les modèles LLM locaux
- Destiné à être déployé sur Windows
- **Scripts d'installation** : `install_zero_obstacle.bat` et `start_zero_obstacle.bat`

### 2. Application exemple : Celery API (`api/app.py`)
- Exemple d'API avec Celery pour traitement asynchrone
- Utilise Redis, OpenAI, et Supabase
- Destiné à être déployé via Docker
- **Démarrage** : `docker-compose up`

## Contenu du dépôt

### Application principale (Zero Obstacle)
- `main.py` : serveur FastAPI avec orchestrateur et agents utilisant Ollama
- `wordpress-plugin/zero-obstacle-agent/zero-obstacle-agent.php` : plugin WordPress minimal pour relayer les questions vers l'orchestrateur
- `install_zero_obstacle.bat` / `start_zero_obstacle.bat` : scripts Windows pour installer les dépendances et démarrer le serveur
- `test_api.py` : tests manuels simples pour vérifier que l'API répond localement

### Application exemple (Celery)
- `api/app.py` : exemple d'API FastAPI avec intégration Celery
- `api/workers/` : workers Celery et scheduler
- `api/connectors/` : connecteurs OpenAI et Supabase
- `docker-compose.yml` : configuration Docker pour l'application Celery
- `api/Dockerfile` : Dockerfile pour l'application Celery

## Prérequis

- Python 3.10+ sur la machine Windows qui héberge l'API.
- Ollama en cours d'exécution avec un modèle disponible (par défaut `llama3.1`).
- Accès réseau entre WordPress (PlanetHoster) et l'API (port 8080 par défaut).

## Mise en route rapide

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
4. **Installer le plugin WordPress**
   - Zipper le dossier `wordpress-plugin/zero-obstacle-agent` puis téléverser-le via l’interface WP.
   - Configurer l’URL de l’API dans « Réglages → Zero Obstacle Agent » (ex. `http://TON_PC:8080`).
   - Ajouter le shortcode `[zero_obstacle_form]` dans une page ou un article.

## Endpoints clés

### Application principale (main.py - port 8080)
- `GET /health` : vérifie que le serveur répond et retourne le modèle Ollama configuré.
- `POST /agent/orchestrate` : route les tâches `pdf_extraction`, `admissibility`, `prefill`, `general` vers les agents dédiés.
- Démos : `GET /demo/admissibility`, `GET /demo/prefill`.

### Application exemple (api/app.py - port 8000)
- `GET /` : health check de l'API Celery
- `POST /enqueue` : enqueue une tâche d'addition pour le worker Celery

## Notes importantes

- Les règles d’admissibilité doivent être fournies explicitement dans les requêtes (`program_rules`), aucune logique juridique n’est inventée.
- Le préremplissage ne devine pas d’informations absentes du profil utilisateur.
- Le parsing JSON des réponses LLM est volontairement simple pour rester un MVP ; prévoir du durcissement pour la production.
