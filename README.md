# iA_GPT_Zero_obstacle

Plateforme MVP d'orchestration d'agents auto-hébergeables pour le projet « Zero Obstacle ».

## Contenu du dépôt

- `main.py` : serveur FastAPI avec orchestrateur et agents (extraction PDF, admissibilité, préremplissage, questions générales) utilisant Ollama.
- `wordpress-plugin/zero-obstacle-agent/zero-obstacle-agent.php` : plugin WordPress minimal pour relayer les questions vers l'orchestrateur.
- `install_zero_obstacle.bat` / `start_zero_obstacle.bat` : scripts Windows pour installer les dépendances et démarrer le serveur.
- `test_api.py` : tests manuels simples pour vérifier que l'API répond localement.

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

- `GET /health` : vérifie que le serveur répond et retourne le modèle Ollama configuré.
- `GET /metrics` : endpoint de monitoring pour Prometheus.
- `POST /agent/orchestrate` : route les tâches `pdf_extraction`, `admissibility`, `prefill`, `general` vers les agents dédiés.
- Démos : `GET /demo/admissibility`, `GET /demo/prefill`.

## Sécurité

L'API est protégée par un système d'API Key. Pour utiliser l'API :

1. Générer une clé : `openssl rand -hex 32`
2. Ajouter dans `.env` : `API_KEY=votre-clé-générée`
3. Inclure dans chaque requête : header `X-API-Key: votre-clé-générée`

Les endpoints `/health`, `/metrics`, `/docs` sont accessibles sans authentification.

## Tests

```bash
# Tests unitaires
pytest tests/ -v

# Tests avec couverture
pytest --cov=main --cov-report=html

# Smoke test
python test_api.py
```

Voir `RUNBOOK.md` pour la documentation opérationnelle complète.

## Notes importantes

- Les règles d’admissibilité doivent être fournies explicitement dans les requêtes (`program_rules`), aucune logique juridique n’est inventée.
- Le préremplissage ne devine pas d’informations absentes du profil utilisateur.
- Le parsing JSON des réponses LLM est volontairement simple pour rester un MVP ; prévoir du durcissement pour la production.
