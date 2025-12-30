# Plan de Déploiement - Legal Ingest Pipeline

## Vue d'ensemble

Ce document décrit le processus de déploiement étape par étape du pipeline d'ingestion légale sur l'architecture distribuée (2 serveurs locaux + PlanetHoster).

## Timeline

- **Phase 1** (Jours 1-3): Infrastructure et configuration
- **Phase 2** (Semaine 1): MVP ingestion fédérale
- **Phase 3** (Semaines 2-4): Extension provinces + régulateurs
- **Phase 4** (Mois 2-6): Municipalités (progressive)

## Prérequis

### Matériel

- **Serveur 1**: PC Windows, 16GB RAM, disque D:\ (4TB disponible)
- **Serveur 2**: PC Windows, 16GB RAM, disque E:\ (4TB disponible)
- **PlanetHoster**: Compte hébergement Canada, accès SSH/Docker

### Logiciels

- Windows 10/11 Pro (pour Hyper-V/WSL2)
- Docker Desktop for Windows
- PowerShell 5.1+
- Git
- Compte GitHub (pour CI/CD)

### Réseau

- Connexion Internet stable (upload >10 Mbps recommandé)
- Ports ouverts: 80, 443, 22 (SSH), 51820 (WireGuard optionnel)
- DNS configuré pour `api.zeroobstacle.ca`

## Phase 1: Infrastructure (Jours 1-3)

### Jour 1: Serveur 1

```powershell
# Cloner le repository
git clone https://github.com/jiwwycaosita/iA_Zero_obstacle.ca.git
cd iA_Zero_obstacle.ca/modules/legal-ingest

# Exécuter le setup
.\scripts\setup-server1.ps1
```

**Checklist:**
- [ ] Docker Desktop installé
- [ ] WSL2 configuré
- [ ] Répertoires créés sur D:\
- [ ] Firewall configuré
- [ ] .env créé et configuré
- [ ] Services démarrés (OpenSearch, Milvus, Workers 1-3)
- [ ] Vérification: `curl http://localhost:9200`

### Jour 2: Serveur 2

```powershell
# Sur Serveur 2
git clone https://github.com/jiwwycaosita/iA_Zero_obstacle.ca.git
cd iA_Zero_obstacle.ca/modules/legal-ingest

.\scripts\setup-server2.ps1
```

**Checklist:**
- [ ] Docker Desktop installé
- [ ] WSL2 configuré
- [ ] Répertoires créés sur E:\
- [ ] Firewall configuré
- [ ] Network partagé avec Serveur 1
- [ ] Services démarrés (Postgres, MinIO, Airflow, Workers 4-6)
- [ ] Vérification: Accès Airflow http://localhost:8080

### Jour 3: PlanetHoster + Tunnel

**Sur PlanetHoster:**

```bash
# Connexion SSH
ssh root@your-server.planethoster.ca

# Upload des fichiers
scp -r modules/legal-ingest root@your-server:/opt/

# Setup
cd /opt/legal-ingest
sudo ./scripts/setup-planethoster.sh
```

**Configuration DNS:**
- Pointer `api.zeroobstacle.ca` vers IP PlanetHoster
- Attendre propagation DNS (15-60 min)

**Tunnel sécurisé:**

```powershell
# Sur Serveur 1 ou 2
.\scripts\tunnel-setup.ps1
```

**Checklist:**
- [ ] API déployée sur PlanetHoster
- [ ] SSL certificat obtenu (Let's Encrypt)
- [ ] API accessible: https://api.zeroobstacle.ca/health
- [ ] Tunnel établi entre serveurs locaux et cloud
- [ ] Test connexion bidirectionnelle

## Phase 2: MVP Ingestion Fédérale (Semaine 1)

### Configuration sources

```yaml
# Éditer src/sources.yaml
# Activer uniquement sources prioritaires:
# - Justice Laws
# - Canada Gazette
# - Supreme Court of Canada
```

### Lancement ingestion

```bash
# Sur Serveur 1
docker exec -it legal_worker1 python -m src.ingest_manager --once
```

### Monitoring

```bash
# Prometheus
http://localhost:9090

# Grafana
http://localhost:3000
# Import dashboard: monitoring/grafana-dashboards/legal-ingest-overview.json
```

**Checklist:**
- [ ] Scrapers testés sur Justice Laws
- [ ] Au moins 50 documents ingérés
- [ ] Documents normalisés et indexés dans OpenSearch
- [ ] Embeddings générés et stockés dans Milvus
- [ ] Métadonnées dans Postgres
- [ ] API retourne résultats de recherche
- [ ] Sync vers PlanetHoster fonctionne

## Phase 3: Provinces + Régulateurs (Semaines 2-4)

### Semaine 2: Ontario + Québec

```yaml
# Activer dans sources.yaml
provinces:
  ontario:
    - name: Ontario e-Laws
  quebec:
    - name: LégisQuébec
```

### Semaine 3: BC + Alberta + Régulateurs

```yaml
provinces:
  british_columbia:
    - name: BC Laws
  alberta:
    - name: Alberta Laws

regulators:
  - name: Canada Revenue Agency
  - name: AMF
  - name: IRCC
```

### Semaine 4: Autres provinces

```yaml
# Activer toutes les provinces restantes
# Ajuster rate limiting si nécessaire
```

**Checklist:**
- [ ] 10+ provinces ingérées
- [ ] 5+ régulateurs ingérés
- [ ] >1000 documents totaux
- [ ] Performance stable (RAM <14GB par serveur)
- [ ] Aucune erreur critique
- [ ] Backup automatique configuré

## Phase 4: Municipalités (Mois 2-6)

### Mois 2: Grandes villes prioritaires

```yaml
municipalities:
  priority_cities:
    - Toronto
    - Montreal
    - Vancouver
    - Calgary
    - Ottawa
```

### Mois 3-6: Extension progressive

- Semaine par semaine, ajouter 50-100 villes
- Monitoring performance
- Ajustement scrapers au besoin

**Checklist:**
- [ ] 5 grandes villes ingérées
- [ ] Pipeline municipal validé
- [ ] Extension à 500 villes (mois 4)
- [ ] Extension à 2000 villes (mois 5)
- [ ] Couverture complète 5000+ villes (mois 6)

## Configuration Backup Automatique

### Windows Task Scheduler

```powershell
# Créer tâche planifiée
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
  -Argument "-File C:\path\to\legal-ingest\scripts\backup-daily.ps1"

$trigger = New-ScheduledTaskTrigger -Daily -At 2am

$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" `
  -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask -TaskName "Legal Ingest Daily Backup" `
  -Action $action -Trigger $trigger -Principal $principal
```

**Checklist:**
- [ ] Backup script testé manuellement
- [ ] Tâche planifiée créée
- [ ] Premier backup réussi
- [ ] Vérification restauration

## Tests de validation

### Tests unitaires

```bash
pytest tests/ -v --cov=src
```

### Tests d'intégration

```bash
# Test end-to-end
python tests/integration/test_e2e.py
```

### Tests de charge

```bash
# Simuler charge avec k6 ou locust
locust -f tests/load/locustfile.py
```

## Monitoring et alertes

### Métriques clés à surveiller

- CPU utilisation (<80%)
- RAM utilisation (<90%)
- Disk I/O
- Network bandwidth
- Documents/heure
- Taux d'erreur (<5%)
- Latence API (<500ms)

### Alertes Prometheus

```yaml
# Exemple alert rules
groups:
  - name: legal_ingest_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(documents_processed_total{status="error"}[5m]) > 0.1
        for: 10m
        annotations:
          summary: "Taux d'erreur élevé"
```

## Rollback et contingence

### Rollback d'une version

```bash
# Arrêter services
docker-compose down

# Restaurer backup
# ... (voir procédure backup)

# Redémarrer avec version précédente
git checkout <previous_commit>
docker-compose up -d
```

### Plan de contingence

1. **Panne Serveur 1**: Basculer workers vers Serveur 2
2. **Panne Serveur 2**: Mode lecture seule sur cache PlanetHoster
3. **Panne réseau**: Mode autonome local, sync différée
4. **Panne PlanetHoster**: Redirection temporaire vers IP locale

## Checklist finale

- [ ] Tous les services opérationnels
- [ ] Tunnel sécurisé stable
- [ ] Backup automatique fonctionnel
- [ ] Monitoring configuré
- [ ] Alertes configurées
- [ ] Documentation à jour
- [ ] Tests passent (>80% coverage)
- [ ] API accessible publiquement
- [ ] Performance acceptable (<500ms)
- [ ] Sécurité validée (SSL, firewall, secrets)

## Support post-déploiement

### Maintenance hebdomadaire

- Vérifier logs erreurs
- Valider backups
- Analyser métriques
- Mettre à jour dépendances

### Maintenance mensuelle

- Review performance
- Optimisation index
- Nettoyage données obsolètes
- Audit sécurité

## Contacts

- **Lead technique**: Jimmy Renaud
- **Support infrastructure**: [à définir]
- **Urgences**: admin@zeroobstacle.ca
