# iA_GPT_Zero_obstacle

Plateforme auto-hébergeable pour orchestrer des agents fiscaux et administratifs via FastAPI/Ollama et un plugin WordPress.

## Contenu principal
- `main.py` : serveur FastAPI avec orchestrateur et agents (PDF, admissibilité, préremplissage, question générale). L'évaluation d'admissibilité est maintenant entièrement déterministe (pas d'appel LLM) pour éviter les hallucinations.
- `install_zero_obstacle.bat` / `start_zero_obstacle.bat` : scripts Windows pour installer les dépendances et lancer l’API.
- `test_api.py` : tests simples pour vérifier la disponibilité de l’API.
- `tests/test_admissibility.py` : tests unitaires qui valident les opérateurs et
  l’éligibilité déterministe sans appel LLM.
- `wordpress-plugin/zero-obstacle-agent/` : plugin WordPress prêt à téléverser.
- `docs/PLAYBOOK_OPTIONS.md` : guide utilisateur et démarrage rapide.
- `app/services/embedding.py` et `app/tasks/vector_tasks.py` : service d’embeddings OpenAI et tâche Celery pour alimenter une table PGVector (Supabase/PostgreSQL).
- `app/admissibility_core.py` : noyau déterministe des règles d’admissibilité, testable sans dépendre de FastAPI/Ollama.

## Démarrage express
1. Sur le PC Windows, exécute `install_zero_obstacle.bat`, puis `start_zero_obstacle.bat`.
2. Vérifie que `http://localhost:8080/health` répond, ou lance `python test_api.py`.
3. Lance `python -m unittest tests/test_admissibility.py` pour valider les règles
   d’admissibilité et les opérateurs pris en charge.
4. Dans WordPress, téléverse le zip du dossier `wordpress-plugin/zero-obstacle-agent/`, configure l’URL API, et ajoute `[zero_obstacle_form]` dans une page.

## Embeddings PGVector (Supabase + Celery)
1. Configure les variables d’environnement côté worker Celery :
   - `OPENAI_API_KEY` (et éventuellement `OPENAI_EMBEDDING_MODEL`)
   - `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY`
2. Assure-toi que la table `vector_chunks` a une contrainte unique sur `program_id` et un index PGVector (ex. IVFFlat).
3. Lance un worker et le scheduler Beat :
   - `celery -A app.tasks.vector_tasks worker --loglevel=info`
   - `celery -A app.tasks.vector_tasks beat --loglevel=info`
4. La tâche planifiée `tasks.update_all_embeddings` lit la table `programs`, génère les embeddings asynchrones via OpenAI et fait un `upsert` massif dans `vector_chunks`.
