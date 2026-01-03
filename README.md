# Zero Obstacle - Plateforme Citoyens

Plateforme d'orchestration d'agents intelligents auto-hébergeable pour le projet « Zero Obstacle ».

## Description du Projet

Zero Obstacle est une plateforme citoyenne qui aide les utilisateurs à naviguer les processus administratifs complexes. Elle intègre plusieurs modules pour:

- **Services financiers et bancaires**: Assistance pour les demandes d'aide financière
- **Services juridiques**: Aide à la compréhension des lois et règlements
- **Extraction et analyse de formulaires PDF**: Analyse automatique de documents administratifs
- **Préremplissage automatique**: Remplissage intelligent de formulaires en ligne
- **Vérification d'admissibilité**: Évaluation technique des critères d'éligibilité aux programmes
- **Assistant conversationnel**: Réponses aux questions générales sur les démarches administratives
- **Calculateur de remorquage**: Estimation détaillée des frais de remorquage selon la province et le type de service
- **Optimisation fiscale avancée**: Analyse complète des programmes gouvernementaux, crédits d'impôt, et stratégies d'optimisation pour maximiser les économies fiscales

## Architecture

L'application utilise:
- **FastAPI**: Framework web moderne et performant
- **Ollama**: Modèles de langage locaux pour préserver la confidentialité
- **pypdf**: Extraction de texte depuis les documents PDF
- **WordPress Plugin**: Interface utilisateur accessible via WordPress

## Contenu du Dépôt

- `main.py`: Serveur FastAPI principal avec orchestrateur et agents spécialisés
  - Agent d'extraction PDF
  - Agent d'admissibilité aux programmes
  - Agent de préremplissage de formulaires
  - Agent conversationnel général
  - Agent calculateur de remorquage
  - Agent d'optimisation fiscale et recherche de programmes gouvernementaux
- `wordpress-plugin/zero-obstacle-agent/`: Plugin WordPress pour connecter la plateforme à votre site
- `Dockerfile`: Configuration Docker pour déploiement containerisé
- `docker-compose.yml`: Orchestration de l'application en conteneurs
- `install_zero_obstacle.bat` / `start_zero_obstacle.bat`: Scripts Windows pour installation et démarrage rapide
- `test_api.py`: Tests simples pour vérifier le fonctionnement de l'API
- `requirements.txt`: Dépendances Python du projet

## Prérequis

### Installation Locale (Windows)
- Python 3.10+ installé sur votre machine Windows
- Ollama en cours d'exécution avec un modèle téléchargé (par défaut `llama3.1`)
  - Télécharger Ollama: https://ollama.ai/
  - Installer un modèle: `ollama pull llama3.1`
- Accès réseau entre WordPress et l'API (port 8080 par défaut)

### Installation Docker
- Docker et Docker Compose installés
- Ollama accessible (peut être sur la machine hôte via `host.docker.internal`)

## Mise en Route

### Option 1: Installation Windows (Locale)

1. **Installer l'API**
   ```bat
   install_zero_obstacle.bat
   ```

2. **Démarrer le serveur**
   ```bat
   start_zero_obstacle.bat
   ```

3. **Vérifier le fonctionnement**
   ```bash
   python test_api.py
   ```

### Option 2: Installation Docker

1. **Créer le fichier .env**
   ```bash
   cp .env.example .env
   ```
   
2. **Ajuster la configuration** (optionnel)
   
   Modifier les variables dans `.env` selon votre environnement:
   - `OLLAMA_URL`: URL de votre instance Ollama
   - `OLLAMA_MODEL`: Modèle à utiliser (défaut: llama3.1)

3. **Démarrer avec Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Vérifier le fonctionnement**
   ```bash
   curl http://localhost:8080/health
   ```

### Installation du Plugin WordPress

1. **Préparer le plugin**
   - Zipper le dossier `wordpress-plugin/zero-obstacle-agent`
   
2. **Installer dans WordPress**
   - Téléverser le zip via « Extensions → Ajouter »
   - Activer le plugin
   
3. **Configurer l'API**
   - Aller dans « Réglages → Zero Obstacle Agent »
   - Entrer l'URL de votre API (ex: `http://VOTRE_IP:8080`)
   
4. **Utiliser le shortcode**
   - Ajouter `[zero_obstacle_form]` dans une page ou un article
   - Les visiteurs peuvent maintenant poser des questions à l'assistant

## API Endpoints

### Endpoints principaux

- `GET /health` - Vérifie que le serveur répond et retourne le modèle Ollama configuré
- `POST /agent/orchestrate` - Route les tâches vers les agents spécialisés

### Endpoints de démonstration

- `GET /demo/admissibility` - Démonstration de vérification d'admissibilité
- `GET /demo/prefill` - Démonstration de préremplissage de formulaire
- `GET /demo/towing` - Démonstration du calculateur de remorquage
- `GET /demo/tax_optimization` - Démonstration de l'optimisation fiscale et recherche de programmes

### Utilisation de l'endpoint d'orchestration

L'endpoint `/agent/orchestrate` accepte différents types de tâches:

#### 1. Extraction de PDF (`pdf_extraction`)
```json
{
  "task": "pdf_extraction",
  "pdf_base64": "<contenu_pdf_en_base64>"
}
```

#### 2. Vérification d'admissibilité (`admissibility`)
```json
{
  "task": "admissibility",
  "user_profile": {
    "age": 35,
    "province": "QC",
    "income": 25000
  },
  "program_rules": [
    {
      "id": "age_min_18",
      "description": "Âge minimum 18 ans",
      "field": "age",
      "operator": ">=",
      "value": 18,
      "required": true
    }
  ]
}
```

#### 3. Préremplissage de formulaire (`prefill`)
```json
{
  "task": "prefill",
  "user_profile": {
    "first_name": "Jean",
    "last_name": "Dupont",
    "email": "jean.dupont@example.com"
  },
  "text": "{\"fields\": [{\"name\": \"first_name\", \"label\": \"Prénom\", \"type\": \"string\"}]}"
}
```

#### 4. Question générale (`general`)
```json
{
  "task": "general",
  "text": "Comment puis-je faire une demande d'aide financière?"
}
```

#### 5. Calculateur de remorquage (`towing_calculator`)
```json
{
  "task": "towing_calculator",
  "towing_data": {
    "vehicle_type": "car",
    "distance_km": 25.5,
    "location": "QC",
    "service_type": "standard",
    "additional_services": ["winch", "flatbed"]
  }
}
```

**Réponse** : Estimation détaillée des frais incluant frais de base, distance, suppléments, taxes, total estimé avec plage de prix (min-max), recommandations pour économiser, et score de fiabilité.

#### 6. Optimisation fiscale et recherche de programmes (`tax_optimization`)
```json
{
  "task": "tax_optimization",
  "tax_data": {
    "province": "QC",
    "income": 65000,
    "filing_status": "married",
    "dependents": 2,
    "business_income": 15000,
    "investment_income": 2000,
    "rrsp_contribution": 5000,
    "rdsp_contribution": 0,
    "years_to_analyze": [2023, 2024, 2025]
  }
}
```

**Réponse complète incluant** :
- **Score de fiabilité** (0-100%) basé sur la complétude des informations
- **Programmes gouvernementaux** : Liste TOUS les programmes fédéraux et provinciaux applicables avec montants estimés
- **Calcul d'impôt détaillé** : Impôt fédéral/provincial, taux marginal/effectif, crédits applicables
- **Optimisation RRSP/REEI** : Contributions optimales, économies d'impôt, subventions gouvernementales
- **Stratégies d'optimisation** : Fractionnement du revenu, déductions manquées, optimisation des placements
- **Analyse comparative** : Scénario actuel vs optimisé avec gains/pertes détaillés
- **Opportunités de contestation** : Décisions administratives contestables, montants à réviser
- **Projections futures** : Impact fiscal sur 3-5 ans
- **Recommandations personnalisées**

**Note importante** : L'utilisateur est responsable de fournir des informations complètes et exactes. Plus les informations sont complètes, plus le score de fiabilité et la précision de l'analyse sont élevés.

## Notes Importantes

### Sécurité et Confidentialité
- **Données locales**: L'utilisation d'Ollama permet de garder toutes les données sur votre infrastructure
- **Pas d'envoi vers le cloud**: Aucune information n'est envoyée à des services tiers
- **CORS**: Configuré en mode permissif pour le MVP - à restreindre en production

### Limitations du MVP
- Les règles d'admissibilité doivent être fournies explicitement dans les requêtes (`program_rules`)
- Aucune logique juridique n'est inventée par le système
- Le préremplissage ne devine pas d'informations absentes du profil utilisateur
- Le parsing JSON des réponses LLM est simple - prévoir du renforcement pour la production

### Prochaines Étapes (Suggestions)
- Ajouter une base de données pour stocker les profils utilisateurs
- Implémenter un système de cache pour les réponses fréquentes
- Ajouter une authentification pour sécuriser l'API
- Créer une interface d'administration pour gérer les règles de programmes
- Intégrer des connecteurs pour les services gouvernementaux
- Améliorer la validation et le traitement des erreurs

## Support et Contribution

Pour toute question ou suggestion d'amélioration, n'hésitez pas à ouvrir une issue sur le dépôt GitHub.

## Licence

Ce projet fait partie de l'initiative Zero Obstacle pour faciliter l'accès aux services administratifs.
