# iA_GPT_Zero_obstacle

Une plateforme capable d’analyser et d’optimiser la situation juridique, financière, fiscale et citoyenne de chaque Canadien : un assistant complet de protection et d’optimisation personnelle.

## Démarrer l'API

1. Installez les dépendances Python :
   ```bash
   pip install -r requirements.txt
   ```
2. Exportez votre clé API OpenAI :
   ```bash
   export OPENAI_API_KEY="votre_cle"
   ```
3. Lancez le serveur :
   ```bash
   uvicorn api.main:app --reload
   ```

L'endpoint `POST /analyze_profile` démontre l'utilisation du `ProfileAgent` avec un mode de prompt sélectionnable. Un endpoint `GET /health` est aussi disponible pour les vérifications d'état.
