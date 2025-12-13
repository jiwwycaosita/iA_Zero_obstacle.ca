# Playbook fiscal — Instructions utilisateur et livrables MVP

Ce dépôt fournit un squelette immédiatement utilisable, auto-hébergeable, pour ton stack WordPress PlanetHoster ↔️ PC Windows (FastAPI + Ollama). Il inclut l’orchestrateur, le plugin WordPress, les scripts Windows, les tests et des démos minimales.

## 1. Faits validés
- Stack 100 % auto-hébergeable : WordPress (PlanetHoster) + FastAPI/Ollama (PC Windows 16 Go RAM).
- Un **`main.py` unique** héberge l’Agent Orchestrateur et les sous-agents (PDF, admissibilité, préremplissage, etc.).
- Livrables attendus :
  1. `main.py` avec API HTTP + agents.
  2. Plugin WordPress prêt pour `wp-content/plugins` (`wordpress-plugin/zero-obstacle-agent/`).
  3. Script `.bat` pour installer et démarrer le serveur (`install_zero_obstacle.bat` et `start_zero_obstacle.bat`).
  4. Tests simples (`test_api.py`).
  5. Démos pour extraction PDF, admissibilité, préremplissage (endpoints `/demo/...`).

## 2. Déductions sûres
- Backend : **FastAPI** (JSON natif, simple) avec Ollama HTTP API (`http://localhost:11434/api/generate`).
- WordPress appelle l’API orchestrateur via `wp_remote_post()` → `http://TON_PC:8080/agent/orchestrate`.
- Les agents sont des fonctions Python routées selon `task` dans le JSON reçu.
- Les démos utilisent des exemples fictifs (pas de droit inventé). Les règles juridiques doivent être fournies par l’utilisateur.

## 3. Limites et hypothèses
- Les règles légales réelles ne sont pas dans le code ; elles doivent être injectées (JSON/BDD/fichiers).
- Le plugin WP est un MVP (pas d’authentification avancée, gestion d’erreurs minimale).
- Le script `.bat` suppose `winget` et Ollama déjà installés (avec `ollama pull llama3.1`).

## 4. Démarrage rapide
1) Copier `main.py`, `install_zero_obstacle.bat`, `start_zero_obstacle.bat` et `test_api.py` sur le PC Windows (ex. `C:\ZeroObstacle_Agents`).
2) Exécuter `install_zero_obstacle.bat` (installe venv + dépendances et crée `.env`).
3) Lancer `start_zero_obstacle.bat` pour démarrer l’API sur `http://0.0.0.0:8080`.
4) Tester localement :
   - `python test_api.py`
   - `curl http://localhost:8080/health`
5) Côté WordPress, zipper `wordpress-plugin/zero-obstacle-agent/` puis téléverser comme extension. Configurer l’URL API dans **Réglages → Zero Obstacle Agent**, puis insérer le shortcode `[zero_obstacle_form]`.

### Tâche d’embeddings Supabase (PGVector)
- Variables d’environnement requises pour le worker : `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (et optionnellement `OPENAI_EMBEDDING_MODEL`).
- Worker Celery : `celery -A app.tasks.vector_tasks worker --loglevel=info`
- Scheduler Beat quotidien : `celery -A app.tasks.vector_tasks beat --loglevel=info`
- La tâche `tasks.update_all_embeddings` parcourt la table `programs`, génère les embeddings OpenAI puis upsert dans `vector_chunks` (clé unique `program_id`, index PGVector IVFFlat recommandé).

## 5. Endpoints clés
- `GET /health` — statut + modèle Ollama.
- `POST /agent/orchestrate` — route les tâches :
  - `pdf_extraction` : base64 PDF → texte brut + schéma de champs proposé.
  - `admissibility` : profil + règles JSON → verdict technique.
  - `prefill` : profil + schéma JSON → valeurs préremplies sans invention.
  - `general` : question générale structurée (pas de création de nouvelles lois).
- Démos : `GET /demo/admissibility` et `GET /demo/prefill`.

## 6. Étapes suivantes possibles
- Ajouter un agent « Programmes Canada » avec schéma JSON standardisé et persistance MySQL/MariaDB.
- Ajouter un mode d’audit (« strict Zéro Obstacle ») avec logs fichier.
- Étendre le plugin WP avec authentification et meilleure gestion d’erreurs.
