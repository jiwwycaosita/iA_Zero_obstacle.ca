# Extraction des données canadiennes

## Vue d'ensemble

Le module d'extraction utilise **Firecrawl** pour crawler automatiquement les sites gouvernementaux canadiens et extraire les données officielles sur les prestations, impôts, services, etc.

## Sources couvertes

### Fédéral
- Prestations (AE, pensions, famille, invalidité)
- Impôts et crédits (ARC)
- Immigration
- Emploi
- Logement
- Open Data Canada

### Provincial
- **Québec**: Aide financière, Revenu Québec, RAMQ, AFE
- **Ontario**: Services sociaux, santé

## Utilisation

### Crawler une URL spécifique
```bash
# Windows
scripts\run_firecrawl.bat single https://www.canada.ca/fr/services/prestations.html

# Linux/macOS
python agents/firecrawl_crawler.py https://www.canada.ca/fr/services/prestations.html
```

### Crawler les sources prioritaires (MVP)
```bash
scripts\run_firecrawl.bat priority
```

### Crawler toutes les sources
```bash
scripts\run_firecrawl.bat all
```

## Structure des données

### Données brutes
`data/can_gov/{url_hash}_{timestamp}.json`

```json
{
  "metadata": {
    "url": "https://...",
    "url_hash": "abc123...",
    "timestamp": "20250115_103000",
    "format": "markdown",
    "extraction_date": "2025-01-15T10:30:00"
  },
  "content": "..."
}
```

### Données normalisées
`data/processed/normalized_{url_hash}.json`

```json
{
  "source_url": "https://...",
  "content_hash": "sha256...",
  "extraction_date": "2025-01-15T10:30:00",
  "processing_date": "2025-01-15T10:35:00",
  "format": "markdown",
  "content": "...",
  "version": "1.0"
}
```

## Workflow complet

1. **Extraction** : `scripts/run_firecrawl.bat priority`
2. **Normalisation** : `python agents/normalization.py`
3. **Vérification** : Check `data/processed/` pour les fichiers normalisés

## Monitoring

Les logs sont dans `data/logs/` :
- `crawl_report_{timestamp}.json` : Rapport de chaque batch
- `error_{url_hash}_{timestamp}.log` : Erreurs individuelles

## Prérequis

- Node.js (pour npx)
- Firecrawl API key dans `.env`
- Python 3.10+

## Troubleshooting

### Timeout
- Augmenter timeout dans `firecrawl_crawler.py` (défaut: 120s)

### Rate limiting
- Firecrawl API a des limites par plan
- Espacer les requêtes si nécessaire

### Erreur 403/robots.txt
- Vérifier que le site autorise le crawling
- Utiliser User-Agent approprié
