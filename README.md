# Zero Obstacle – squelette agents + plugin WordPress

Cette base fournit un orchestrateur FastAPI auto-hébergeable (avec Ollama), un plugin WordPress minimal pour interroger l'orchestrateur, des scripts Windows pour installer/démarrer et un petit script de test.

## Contenu du dépôt
- `main.py` : serveur FastAPI avec agents orchestrateur, extraction PDF, admissibilité (évaluée localement, sans LLM), préremplissage déterministe et démos. L'extraction PDF boucle sur le texte en morceaux pour ingérer entièrement les formulaires volumineux.
- `wordpress-plugin/zero-obstacle-agent/zero-obstacle-agent.php` : plugin WordPress prêt à zipper et déposer dans `wp-content/plugins`.
- `install_zero_obstacle.bat` : script Windows pour installer Python (via winget si absent), créer un venv et installer les dépendances.
- `start_zero_obstacle.bat` : démarre le serveur `uvicorn` sur le port 8080.
- `test_api.py` : tests rapides pour vérifier que l'API locale répond.

## Démarrage rapide (Windows)
1. Place `main.py`, `install_zero_obstacle.bat` et `start_zero_obstacle.bat` dans un dossier (ex. `C:\\ZeroObstacle_Agents`).
2. (Optionnel) Crée un fichier `.env` avec vos valeurs ; sinon `install_zero_obstacle.bat` en génère un :
   ```
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.1
   ```
3. Exécute `install_zero_obstacle.bat` pour installer les dépendances dans `venv`.
4. Lance `start_zero_obstacle.bat` pour démarrer l'API sur `http://0.0.0.0:8080`.

## Utilisation du plugin WordPress
1. Zipper le dossier `wordpress-plugin/zero-obstacle-agent/` puis téléverser l'archive dans WordPress (`Extensions -> Ajouter -> Téléverser`).
2. Dans `Réglages -> Zero Obstacle Agent`, définir l'URL de l'API (ex. `http://TON_PC:8080`).
3. Ajouter le shortcode `[zero_obstacle_form]` dans une page ou un article pour envoyer des questions à l'orchestrateur (`task=general`).

## Points d'entrée API principaux
- `GET /health` : état du service et modèle utilisé.
- `POST /agent/orchestrate` avec `task` parmi `pdf_extraction`, `admissibility`, `prefill`, `general`.
- Démos :
  - `GET /demo/admissibility`
  - `GET /demo/prefill`

## Tester localement
Avec l'environnement virtuel activé :
```bash
python test_api.py
```

Pour vérifier manuellement :
```bash
curl http://localhost:8080/health
curl -X POST http://localhost:8080/agent/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"task": "general", "text": "Bonjour, que peux-tu faire ?"}'
```

## Notes
- L'orchestration s'appuie sur l'API Ollama (`/api/generate`) pour les tâches de génération (PDF structuré, réponses générales). Assurez-vous qu'Ollama est installé et qu'un modèle (par défaut `llama3.1`) est disponible.
- L'admissibilité et le préremplissage utilisent désormais une logique locale déterministe (pas d'appel au modèle) afin de ne jamais inventer d'informations.
- Les règles d'admissibilité et les schémas de formulaire fournis sont des exemples purement techniques, à remplacer par des règles et schémas officiels.
