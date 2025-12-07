# iA_GPT_Zero_obstacle

Base de travail pour l'orchestrateur Zéro Obstacle, utilisable en auto-hébergement sur PC Windows (FastAPI + Ollama) avec un plugin WordPress prêt à l'emploi.

## Contenu principal
- `main.py` : serveur FastAPI avec agents (extraction PDF, admissibilité, préremplissage, général) appelant Ollama via HTTP.
- `install_zero_obstacle.bat` / `start_zero_obstacle.bat` : scripts Windows pour installer les dépendances et démarrer le serveur.
- `test_api.py` : vérifications rapides des endpoints `/health` et `/agent/orchestrate`.
- `wordpress/zero-obstacle-agent/` : plugin WordPress qui appelle l'orchestrateur (shortcode `[zero_obstacle_form]`).
- `prompts/` et `api/` : composants hérités de la première version (Docker + Celery + OpenAI/Supabase) laissés pour compatibilité éventuelle.

## Démarrage rapide (PC Windows + Ollama)
1. Installer Ollama et télécharger un modèle, par exemple :
   ```powershell
   ollama pull llama3.1
   ```
2. Copier ce dépôt sur votre PC et lancer :
   ```bat
   install_zero_obstacle.bat
   start_zero_obstacle.bat
   ```
3. L'API répond sur `http://localhost:8080`. Endpoints utiles :
   - `/health`
   - `/agent/orchestrate` (tasks : `pdf_extraction`, `admissibility`, `prefill`, `general`)
   - `/demo/admissibility`, `/demo/prefill`, `/demo/pdf`

## Tester rapidement
```bash
python test_api.py
```

## Plugin WordPress
1. Zipper le dossier `wordpress/zero-obstacle-agent` et téléverser-le dans `wp-content/plugins` via l'interface d'extensions.
2. Dans Réglages > Zero Obstacle Agent, définir l'URL FastAPI (ex : `http://VOTRE_PC:8080`).
3. Ajouter le shortcode `[zero_obstacle_form]` dans une page pour relayer les questions vers l'agent.

## Variables d'environnement
Référence dans `.env.example` :
- `OLLAMA_URL`, `OLLAMA_MODEL` pour l'usage local.
- Variables OpenAI/Supabase/Redis conservées pour l'ancienne pile Docker (si vous en avez besoin).

## Ancienne pile Docker (optionnelle)
Les fichiers `docker-compose.yml`, `api/`, et `prompts/` proviennent de la première itération (FastAPI + Celery + Redis + Supabase + OpenAI). Ils peuvent être conservés ou supprimés selon vos besoins ; la nouvelle approche n'en dépend pas.
