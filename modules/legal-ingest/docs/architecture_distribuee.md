# Architecture Distribuée - Legal Ingest Pipeline

## Vue d'ensemble

L'architecture du pipeline d'ingestion légale est conçue pour gérer des volumes importants de documents tout en respectant les contraintes de ressources (16GB RAM par serveur local) et d'hébergement (Canada obligatoire).

## Architecture globale

```
┌──────────────────────────────────────────────────────────┐
│                    Internet Public                        │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ HTTPS (443)
                         │
┌────────────────────────▼─────────────────────────────────┐
│              PlanetHoster (Canada)                        │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Nginx Reverse Proxy (SSL/TLS)                      │  │
│  │  - SSL termination (Let's Encrypt)                 │  │
│  │  - Rate limiting                                    │  │
│  │  - CORS headers                                     │  │
│  └──────────────────┬─────────────────────────────────┘  │
│                     │                                     │
│  ┌──────────────────▼─────────────────────────────────┐  │
│  │ FastAPI Application                                │  │
│  │  - REST API endpoints                              │  │
│  │  - Recherche full-text + sémantique                │  │
│  │  - Authentification JWT (optionnel)                │  │
│  │  - Cache Redis (optionnel)                         │  │
│  └──────────────────┬─────────────────────────────────┘  │
│                     │                                     │
│  ┌──────────────────▼─────────────────────────────────┐  │
│  │ Postgres Cache (léger)                             │  │
│  │  - Métadonnées documents (sync depuis local)       │  │
│  │  - Index sur: jurisdiction, category, language     │  │
│  │  - Taille: ~2-5 GB                                 │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  Ressources: 2-4 GB RAM, 10-20 GB stockage               │
└────────────────────────┬─────────────────────────────────┘
                         │
                         │ SSH Tunnel / WireGuard VPN
                         │ (chiffré, authentifié)
                         │
        ┌────────────────┴────────────────┐
        │                                 │
┌───────▼──────────┐            ┌────────▼─────────┐
│  Serveur Local 1 │            │ Serveur Local 2  │
│   (16 GB RAM)    │            │  (16 GB RAM)     │
│   Windows 10/11  │            │  Windows 10/11   │
└──────────────────┘            └──────────────────┘
```

## Serveur Local 1 - Search & Embeddings

### Responsabilités

1. **Indexation full-text** (OpenSearch)
2. **Stockage embeddings** (Milvus)
3. **Workers d'ingestion** (1-3)

### Composants

```
┌─────────────────────────────────────────┐
│         Serveur Local 1 (16GB)          │
├─────────────────────────────────────────┤
│                                         │
│  OpenSearch (8GB heap)                  │
│  ├── Index: legal_documents             │
│  ├── Mapping: title, content, metadata  │
│  ├── Analyzers: FR + EN                 │
│  └── Plugins: ICU, analysis-phonetic    │
│                                         │
│  Milvus Standalone (4GB)                │
│  ├── Collection: document_embeddings    │
│  ├── Dimension: 384 (MiniLM)            │
│  ├── Index: IVF_FLAT                    │
│  └── Metric: L2 distance                │
│                                         │
│  Worker 1 (2GB) - Scraper               │
│  ├── Justice Laws                       │
│  ├── Canada Gazette                     │
│  └── Supreme Court                      │
│                                         │
│  Worker 2 (2GB) - Normalizer            │
│  ├── PDF → text extraction              │
│  ├── HTML cleaning                      │
│  └── Metadata extraction                │
│                                         │
│  Worker 3 (2GB) - Embeddings            │
│  ├── Sentence-transformers              │
│  ├── Batch processing                   │
│  └── Milvus upsert                      │
│                                         │
└─────────────────────────────────────────┘
         │                          │
         ▼ (volumes)                ▼
  D:\legal-ingest\          Logs, metrics
  ├── opensearch-data/
  ├── milvus-data/
  ├── etcd/
  ├── raw-data/
  └── logs/
```

### Allocation mémoire détaillée

| Composant      | RAM  | Justification                           |
|----------------|------|-----------------------------------------|
| OpenSearch     | 8 GB | Heap pour indexation et recherche       |
| Milvus         | 4 GB | Vecteurs en mémoire pour perf           |
| Worker 1       | 2 GB | HTTP client + parsing HTML              |
| Worker 2       | 2 GB | PDF processing + normalization          |
| Worker 3       | 2 GB | Model embeddings + batch                |
| **Total**      | **18 GB** | **Excède légèrement 16GB**          |

**Optimisations nécessaires:**
- Réduire OpenSearch heap à 6-7 GB si nécessaire
- Limiter taille batch embeddings
- Monitoring actif swap/paging

## Serveur Local 2 - Storage & Orchestration

### Responsabilités

1. **Base de données master** (Postgres)
2. **Stockage objet** (MinIO)
3. **Orchestration** (Airflow)
4. **Workers sync & monitoring** (4-6)

### Composants

```
┌─────────────────────────────────────────┐
│         Serveur Local 2 (16GB)          │
├─────────────────────────────────────────┤
│                                         │
│  Postgres 15 (4GB)                      │
│  ├── DB: legal_data (master)            │
│  ├── Tables:                            │
│  │   - documents                        │
│  │   - document_versions                │
│  │   - sources                          │
│  │   - scraping_jobs                    │
│  ├── Extensions: pg_trgm, uuid-ossp     │
│  └── Replication: async vers PH         │
│                                         │
│  MinIO (2GB)                            │
│  ├── Bucket: legal-documents            │
│  ├── Stockage: PDF, HTML originaux      │
│  ├── Versioning: enabled                │
│  └── Lifecycle: 90 days retention       │
│                                         │
│  Airflow (4GB)                          │
│  ├── Scheduler                          │
│  ├── Webserver                          │
│  ├── DAGs:                              │
│  │   - daily_ingestion                  │
│  │   - weekly_full_scan                 │
│  │   - monthly_cleanup                  │
│  └── Backend: Postgres                  │
│                                         │
│  Redis (512MB)                          │
│  ├── Queue backend Airflow              │
│  └── Cache optionnel                    │
│                                         │
│  Worker 4 (2GB) - Storage               │
│  Worker 5 (2GB) - Sync PlanetHoster     │
│  Worker 6 (2GB) - Monitoring            │
│                                         │
└─────────────────────────────────────────┘
         │
         ▼ (volumes)
  E:\legal-ingest\
  ├── postgres-data/
  ├── minio-data/
  ├── snapshots/
  └── logs/
```

### Allocation mémoire détaillée

| Composant      | RAM    | Justification                         |
|----------------|--------|---------------------------------------|
| Postgres       | 4 GB   | shared_buffers + effective_cache      |
| MinIO          | 2 GB   | Object storage overhead               |
| Airflow        | 4 GB   | Scheduler + Webserver + Workers       |
| Redis          | 512 MB | Queue backend                         |
| Worker 4       | 2 GB   | File operations + compression         |
| Worker 5       | 2 GB   | DB sync + network                     |
| Worker 6       | 2 GB   | Metrics collection                    |
| **Total**      | **16.5 GB** | **Légèrement au-dessus budget**  |

**Optimisations:**
- Postgres: réduire shared_buffers à 2GB si nécessaire
- Airflow: mode LocalExecutor (pas CeleryExecutor)
- Limiter workers concurrents

## Flux de données

### 1. Ingestion

```
┌─────────┐
│  Source │ (Justice Laws, etc.)
└────┬────┘
     │ HTTP/HTTPS
     ▼
┌─────────────┐
│  Scraper    │ (Worker 1, Server 1)
│  (HTML)     │
└──────┬──────┘
       │ Raw HTML/PDF
       ▼
┌──────────────┐
│  Normalizer  │ (Worker 2, Server 1)
│  (Clean text)│
└──────┬───────┘
       │ Normalized JSON
       ├────────────────────┐
       ▼                    ▼
┌──────────────┐    ┌──────────────┐
│  OpenSearch  │    │  Embeddings  │ (Worker 3, Server 1)
│  (Index)     │    │  (Milvus)    │
└──────────────┘    └──────────────┘
       │                    │
       └────────┬───────────┘
                ▼
        ┌──────────────┐
        │  Postgres    │ (Server 2)
        │  (Metadata)  │
        └──────┬───────┘
               │ Sync
               ▼
        ┌──────────────┐
        │  PlanetHoster│
        │  (Cache)     │
        └──────────────┘
```

### 2. Recherche

```
┌─────────┐
│  Client │
└────┬────┘
     │ HTTPS
     ▼
┌─────────────────┐
│  API (PH)       │
│  FastAPI        │
└────┬────────────┘
     │ Tunnel SSH/WG
     │
     ├──────────────────┐
     ▼                  ▼
┌──────────────┐  ┌──────────────┐
│ OpenSearch   │  │   Milvus     │
│ (Full-text)  │  │ (Semantic)   │
└──────┬───────┘  └──────┬───────┘
       │                 │
       └────────┬────────┘
                ▼
         ┌─────────────┐
         │  Merge &    │
         │  Rank       │
         └──────┬──────┘
                │ Results
                ▼
         ┌─────────────┐
         │  Response   │
         └─────────────┘
```

## Sécurité

### 1. Tunnel sécurisé

**Option A: WireGuard VPN**

```
PlanetHoster (10.0.0.1)
    │
    │ WireGuard (UDP 51820)
    │ Chiffrement: ChaCha20-Poly1305
    │ Authentification: Clés publiques
    │
    ├─── Server 1 (10.0.0.2)
    └─── Server 2 (10.0.0.3)
```

**Option B: SSH Reverse Tunnel**

```
PlanetHoster
    │
    │ SSH (Port 22)
    │ ├── Reverse tunnel: Postgres (15432 → 5432)
    │ ├── Reverse tunnel: OpenSearch (19200 → 9200)
    │ └── Reverse tunnel: Milvus (29530 → 19530)
    │
    └─── Server 1 ou 2
```

### 2. Firewall

**Serveur Local 1:**
- Entrée: SSH (22), WireGuard (51820)
- Sortie: HTTP/HTTPS (80/443)
- Blocage: Tous les autres ports

**Serveur Local 2:**
- Entrée: SSH (22), WireGuard (51820)
- Sortie: HTTP/HTTPS (80/443)
- Blocage: Tous les autres ports

**PlanetHoster:**
- Entrée: HTTP (80), HTTPS (443), SSH (22)
- Sortie: Tunnel vers serveurs locaux
- Blocage: Tous les autres ports

### 3. Authentification

- **API**: JWT tokens (optionnel pour MVP)
- **Tunnel**: Clés SSH ou WireGuard
- **Databases**: Mots de passe forts (>20 chars)
- **MinIO**: Access/Secret keys

### 4. Chiffrement

- **En transit**: TLS 1.3 (API), SSH/WireGuard (tunnel)
- **Au repos**: Chiffrement disk Windows (BitLocker optionnel)

## Scalabilité

### Limites actuelles

| Ressource      | Limite        | Impact                                |
|----------------|---------------|---------------------------------------|
| RAM Server 1   | 16 GB         | Max ~100K documents indexés           |
| RAM Server 2   | 16 GB         | Max ~500K métadonnées                 |
| Disk Server 1  | 4 TB          | Max ~10-15M documents (avec compress) |
| Disk Server 2  | 4 TB          | Max ~5-10M documents originaux        |
| Network upload | ~10 Mbps      | Sync rate ~1 GB/heure                 |

### Pistes d'évolution

1. **Court terme (6 mois)**
   - Ajouter RAM (32GB par serveur): +150%
   - SSD NVMe: +300% I/O performance

2. **Moyen terme (1 an)**
   - Serveur 3 dédié (Milvus seul): +scalabilité embeddings
   - Cluster OpenSearch 3 nodes: +résilience

3. **Long terme (2+ ans)**
   - Migration cloud (AWS Canada, GCP Montreal)
   - Kubernetes orchestration
   - Managed services (RDS, OpenSearch Service)

## Monitoring et observabilité

### Métriques systèmes

- **CPU**: utilisation par container
- **RAM**: usage + swap
- **Disk**: I/O, latency, free space
- **Network**: bandwidth in/out, latency

### Métriques applicatives

- **Documents**: count, rate, errors
- **Scrapers**: success rate, duration
- **API**: requests/sec, latency, errors
- **Sync**: lag, throughput

### Alertes

1. RAM >90% → Email + Slack
2. Disk >85% → Email
3. Error rate >5% → Email + Slack
4. API latency >1s → Slack
5. Sync lag >1h → Email

## Haute disponibilité (optionnel)

Pour MVP: **pas de HA**, acceptable pour usage interne.

Pour production:
- Load balancer (HAProxy, Nginx)
- Postgres réplication (streaming)
- OpenSearch cluster (3+ nodes)
- Milvus distributed mode
- API multi-instances

## Coûts estimés

| Poste              | Coût mensuel | Annuel  |
|--------------------|--------------|---------|
| PlanetHoster       | $25-60       | $300-720|
| Électricité (2 PC) | $20-30       | $240-360|
| Internet           | $0 (inclus)  | $0      |
| **Total**          | **$45-90**   | **$540-1080** |

## Références

- [OpenSearch Documentation](https://opensearch.org/docs/)
- [Milvus Documentation](https://milvus.io/docs)
- [Airflow Documentation](https://airflow.apache.org/docs/)
- [WireGuard Documentation](https://www.wireguard.com/quickstart/)
