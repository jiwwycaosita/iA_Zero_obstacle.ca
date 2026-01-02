# Legal Ingest Pipeline

Système d'ingestion 24/7 pour collecter, normaliser, historiser et exposer l'ensemble des textes légaux canadiens (fédéral, provinces, municipalités, jurisprudence, régulateurs).

## Vue d'ensemble

Ce module implémente une architecture distribuée pour l'ingestion massive de documents légaux canadiens avec:

- **Scraping automatisé** des sources fédérales, provinciales et municipales
- **Normalisation** des documents (PDF, HTML, XML) vers un format canonique
- **Versioning** et historisation complète des changements
- **Recherche full-text** (OpenSearch) et **sémantique** (Milvus/embeddings)
- **Support bilingue** (français/anglais)
- **Architecture distribuée** : serveurs locaux (16GB RAM chacun) + PlanetHoster (cloud Canada)

## Architecture

```
PlanetHoster (Canada)
├── API FastAPI (recherche, consultation)
├── UI Next.js (interface utilisateur)
└── Postgres léger (cache métadonnées)
        │
        │ VPN/SSH tunnel sécurisé
        │
    ┌───┴────┬────────────────┐
    │        │                │
Serveur 1    Serveur 2     Sync
(16GB RAM)   (16GB RAM)    
├── OpenSearch  ├── Postgres master
├── Milvus      ├── MinIO (S3)
├── Workers 1-3 ├── Airflow
└── Disque 4TB  └── Workers 4-6
```

## Démarrage rapide

### Serveur Local 1 (OpenSearch + Milvus + Workers)

```powershell
cd modules/legal-ingest
.\scripts\setup-server1.ps1
```

### Serveur Local 2 (Postgres + MinIO + Airflow)

```powershell
cd modules/legal-ingest
.\scripts\setup-server2.ps1
```

### PlanetHoster (API + Cache)

```bash
cd /opt/legal-ingest
sudo ./scripts/setup-planethoster.sh
```

### Configuration du tunnel sécurisé

```powershell
.\scripts\tunnel-setup.ps1
```

## Configuration

Copiez `.env.example` vers `.env` et configurez:

```env
# Bases de données
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=your_secure_password

# OpenSearch
OPENSEARCH_PASSWORD=your_secure_password

# MinIO
MINIO_SECRET_KEY=your_secure_key

# API
API_SECRET_KEY=your_secret_key
JWT_SECRET=your_jwt_secret

# CanLII (optionnel)
CANLII_API_KEY=your_api_key
```

## Sources de données

Voir `src/sources.yaml` pour la liste complète des sources configurées:

- **Fédéral**: Justice Laws, Canada Gazette, Supreme Court, CanLII
- **Provinces**: Ontario, Québec, BC, Alberta, Saskatchewan, Manitoba, etc.
- **Régulateurs**: CRA, AMF, IRCC, OSFI, FCAC
- **Municipalités**: Toronto, Montréal, Vancouver, Calgary, Ottawa, etc.

## Utilisation

### Démarrer l'ingestion

```bash
# Mode daemon (24/7)
python -m src.ingest_manager

# Single run
python -m src.ingest_manager --once
```

### API

```bash
# Démarrer l'API
python -m src.api

# Endpoints disponibles:
# GET  /health
# POST /search
# GET  /document/{id}
# GET  /jurisdictions
# GET  /history/{id}
# GET  /stats
```

### Synchronisation vers PlanetHoster

```bash
python -m src.sync_to_planethoster
```

### Backup

```powershell
# Backup manuel
.\scripts\backup-daily.ps1

# Configuration backup automatique (Task Scheduler)
# Voir docs/deployment_plan.md
```

## Tests

```bash
# Installer les dépendances de test
pip install pytest pytest-asyncio

# Exécuter tous les tests
pytest

# Tests spécifiques
pytest tests/test_scrapers.py -v
pytest tests/test_normalizer.py -v
pytest tests/test_api.py -v

# Avec coverage
pytest --cov=src --cov-report=html
```

## Monitoring

### Prometheus

Métriques disponibles sur `http://localhost:9090`

- `documents_processed_total` - Documents traités par source
- `scraping_duration_seconds` - Durée du scraping
- `active_scrapers` - Scrapers actifs
- `queue_size` - Taille de la file d'attente

### Grafana

Dashboard disponible sur `http://localhost:3000`

Import: `monitoring/grafana-dashboards/legal-ingest-overview.json`

### Logs

```bash
# Logs Docker Compose
docker-compose -f docker-compose-local-server1.yml logs -f

# Logs applicatifs
tail -f logs/legal_ingest.log
```

## Documentation

- [Plan de déploiement](docs/deployment_plan.md)
- [Architecture distribuée](docs/architecture_distribuee.md)
- [Conformité légale](docs/legal_compliance.md)
- [Inventaire des sources](docs/sources_inventory.md)

## Dépannage

### Les services ne démarrent pas

```bash
# Vérifier Docker
docker ps
docker-compose ps

# Vérifier les logs
docker-compose logs <service_name>

# Redémarrer les services
docker-compose restart
```

### Problèmes de connexion

```bash
# Tester la connexion Postgres
docker exec -it legal_postgres psql -U legal_ingest -d legal_data

# Tester OpenSearch
curl http://localhost:9200

# Tester Milvus
telnet localhost 19530
```

### Performances lentes

1. Vérifier utilisation RAM: `docker stats`
2. Ajuster les limites de mémoire dans `docker-compose-*.yml`
3. Optimiser les index OpenSearch
4. Réduire le nombre de workers concurrents

## Contribuer

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## Approbation légale

Voir `legal_approval_signed.txt` pour l'approbation officielle d'ingestion des contenus légaux canadiens.

## Support

Pour toute question ou problème:
- Ouvrir une issue sur GitHub
- Consulter la documentation dans `/docs`
- Contact: admin@zeroobstacle.ca

## Roadmap

- [x] Phase 1: Infrastructure de base (serveurs, Docker, networking)
- [x] Phase 2: Scrapers fédéraux (Justice Laws, Canada Gazette, SCC)
- [ ] Phase 3: Scrapers provinciaux (Ontario, Québec, BC, etc.)
- [ ] Phase 4: Scrapers municipaux (5000+ villes)
- [ ] Phase 5: API GraphQL avancée
- [ ] Phase 6: UI React/Next.js
- [ ] Phase 7: ML pour classification automatique
- [ ] Phase 8: Alertes et notifications sur changements
