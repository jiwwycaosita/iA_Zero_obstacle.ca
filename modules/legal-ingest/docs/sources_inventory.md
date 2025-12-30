# Inventaire des Sources - Legal Ingest Pipeline

## Vue d'ensemble

Ce document maintient l'inventaire complet de toutes les sources de contenus légaux canadiens configurées pour ingestion dans le système Zéro Obstacle.

**Dernière mise à jour**: 2025-12-30

## Sources Fédérales (4)

### 1. Justice Laws - Lois consolidées

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **Nom officiel**   | Justice Laws Website                      |
| **URL**            | https://laws-lois.justice.gc.ca/          |
| **Type contenu**   | Lois et règlements fédéraux consolidés    |
| **Format**         | HTML, PDF                                 |
| **Langues**        | Français, Anglais                         |
| **Fréquence MAJ**  | Quotidienne                               |
| **API disponible** | Non (scraping HTML)                       |
| **Licence**        | Gouvernement ouvert - Canada              |
| **Priorité**       | 1 (Critique)                              |
| **Estimé docs**    | ~500 lois + 3000 règlements               |
| **Rate limit**     | 2 secondes                                |
| **robots.txt**     | Respecté                                  |
| **Contact**        | info@justice.gc.ca                        |

**Notes techniques**:
- Structure HTML stable
- Index alphabétique disponible
- Sections numérotées
- Métadonnées riches (date consolidation, loi habilitante)

### 2. Canada Gazette - Gazette officielle

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **Nom officiel**   | Canada Gazette                            |
| **URL**            | https://www.gazette.gc.ca/                |
| **Type contenu**   | Publications officielles (avis, décrets)  |
| **Format**         | HTML, PDF, RSS                            |
| **Langues**        | Français, Anglais                         |
| **Fréquence MAJ**  | Hebdomadaire (mercredi)                   |
| **API disponible** | RSS feed                                  |
| **Licence**        | Gouvernement ouvert - Canada              |
| **Priorité**       | 1 (Critique)                              |
| **Estimé docs**    | ~100-200 par semaine                      |
| **Rate limit**     | 2 secondes                                |
| **robots.txt**     | Respecté                                  |
| **Contact**        | gazette@canada.ca                         |

**Notes techniques**:
- RSS feed pour notifications
- Archive complète disponible
- PDF haute qualité
- Métadonnées structurées (type, date publication)

### 3. Supreme Court of Canada - Jurisprudence

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **Nom officiel**   | Supreme Court of Canada                   |
| **URL**            | https://www.scc-csc.ca/                   |
| **Type contenu**   | Jugements et décisions                    |
| **Format**         | HTML, PDF                                 |
| **Langues**        | Français, Anglais                         |
| **Fréquence MAJ**  | Variable (suivant calendrier cours)       |
| **API disponible** | Non                                       |
| **Licence**        | Gouvernement ouvert - Canada              |
| **Priorité**       | 1 (Critique)                              |
| **Estimé docs**    | ~60-80 par année, archive complète        |
| **Rate limit**     | 3 secondes                                |
| **robots.txt**     | Respecté                                  |
| **Contact**        | reception@scc-csc.ca                      |

**Notes techniques**:
- Archive depuis 1876
- Motifs intégraux disponibles
- Résumés et mots-clés
- Références jurisprudence citée

### 4. CanLII - Institut juridique

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **Nom officiel**   | Canadian Legal Information Institute      |
| **URL**            | https://www.canlii.org/                   |
| **Type contenu**   | Jurisprudence multi-juridictions          |
| **Format**         | HTML, API (avec clé)                      |
| **Langues**        | Français, Anglais                         |
| **Fréquence MAJ**  | Quotidienne                               |
| **API disponible** | Oui (requiert clé, négociation)           |
| **Licence**        | CC BY-NC-SA (non commercial)              |
| **Priorité**       | 1 (Critique)                              |
| **Estimé docs**    | >3 millions de décisions                  |
| **Rate limit**     | 5 secondes (ou selon API)                 |
| **robots.txt**     | Respecté                                  |
| **Contact**        | feedback@canlii.org                       |
| **Statut négo**    | À négocier (usage commercial)             |

**Notes techniques**:
- API REST disponible avec authentification
- Bulk download possible avec accord
- Métadonnées normalisées
- Recherche avancée intégrée

## Sources Provinciales (13)

### Ontario - e-Laws

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://www.ontario.ca/laws               |
| **Type**           | Lois et règlements Ontario                |
| **Format**         | HTML, XML                                 |
| **Langues**        | Anglais, Français                         |
| **Fréquence**      | Quotidienne                               |
| **Licence**        | Gouvernement ouvert - Ontario             |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~600 lois + 1000 règlements               |

### Québec - LégisQuébec

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | http://legisquebec.gouv.qc.ca/            |
| **Type**           | Lois et règlements Québec                 |
| **Format**         | HTML                                      |
| **Langues**        | Français, Anglais (partiel)               |
| **Fréquence**      | Quotidienne                               |
| **Licence**        | LiLiQ-P                                   |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~900 lois + 2500 règlements               |

### British Columbia - BC Laws

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://www.bclaws.gov.bc.ca/             |
| **Type**           | Lois et règlements BC                     |
| **Format**         | HTML, XML                                 |
| **Langues**        | Anglais                                   |
| **Fréquence**      | Quotidienne                               |
| **Licence**        | Open Government - BC                      |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~500 lois + 800 règlements                |

### Alberta - Alberta Laws

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://www.qp.alberta.ca/                |
| **Type**           | Lois et règlements Alberta                |
| **Format**         | HTML, PDF                                 |
| **Langues**        | Anglais                                   |
| **Fréquence**      | Hebdomadaire                              |
| **Priorité**       | 3                                         |
| **Estimé docs**    | ~400 lois + 600 règlements                |

### Autres provinces

| Province              | URL                                  | Priorité | Langue |
|-----------------------|--------------------------------------|----------|--------|
| Saskatchewan          | https://www.qp.gov.sk.ca/            | 3        | EN     |
| Manitoba              | https://web2.gov.mb.ca/laws/         | 3        | EN, FR |
| New Brunswick         | https://laws.gnb.ca/                 | 3        | EN, FR |
| Nova Scotia           | https://nslegislature.ca/            | 3        | EN     |
| Prince Edward Island  | https://www.princeedwardisland.ca/   | 3        | EN     |
| Newfoundland Labrador | https://www.assembly.nl.ca/          | 3        | EN     |
| Yukon                 | https://laws.yukon.ca/               | 4        | EN, FR |
| Northwest Territories | https://www.justice.gov.nt.ca/       | 4        | EN, FR |
| Nunavut               | https://www.gov.nu.ca/               | 4        | EN, FR |

## Régulateurs Fédéraux (5)

### CRA - Canada Revenue Agency

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://www.canada.ca/en/revenue-agency   |
| **Type**           | Guides fiscaux, interprétations           |
| **Format**         | HTML, PDF                                 |
| **Langues**        | FR, EN                                    |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~1000 publications                        |

### AMF - Autorité des marchés financiers (QC)

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://lautorite.qc.ca/                  |
| **Type**           | Réglementation marchés financiers         |
| **Format**         | HTML, PDF                                 |
| **Langues**        | FR, EN                                    |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~500 documents                            |

### IRCC - Immigration Canada

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://www.canada.ca/en/immigration      |
| **Type**           | Guides immigration, directives            |
| **Format**         | HTML, PDF                                 |
| **Langues**        | FR, EN                                    |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~800 documents                            |

### OSFI - Superintendent Financial Institutions

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://www.osfi-bsif.gc.ca/              |
| **Type**           | Réglementation institutions financières   |
| **Format**         | HTML, PDF                                 |
| **Langues**        | FR, EN                                    |
| **Priorité**       | 3                                         |
| **Estimé docs**    | ~400 documents                            |

### FCAC - Financial Consumer Agency

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://www.canada.ca/en/financial        |
| **Type**           | Protection consommateurs financiers       |
| **Format**         | HTML, PDF                                 |
| **Langues**        | FR, EN                                    |
| **Priorité**       | 3                                         |
| **Estimé docs**    | ~300 documents                            |

## Municipalités - Villes Prioritaires (5)

### Toronto

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://www.toronto.ca/                   |
| **Type**           | Règlements municipaux                     |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~500 règlements                           |

### Montréal

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://montreal.ca/                      |
| **Type**           | Règlements municipaux                     |
| **Langues**        | FR, EN                                    |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~800 règlements                           |

### Vancouver

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://vancouver.ca/                     |
| **Type**           | Bylaws                                    |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~400 règlements                           |

### Calgary

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://www.calgary.ca/                   |
| **Type**           | Bylaws                                    |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~300 règlements                           |

### Ottawa

| Propriété          | Valeur                                    |
|--------------------|-------------------------------------------|
| **URL**            | https://ottawa.ca/                        |
| **Type**           | Règlements municipaux                     |
| **Langues**        | FR, EN                                    |
| **Priorité**       | 2                                         |
| **Estimé docs**    | ~400 règlements                           |

## Statistiques Globales

| Catégorie      | Sources | Docs estimés |
|----------------|---------|--------------|
| Fédéral        | 4       | ~50,000      |
| Provincial     | 13      | ~25,000      |
| Régulateurs    | 5       | ~3,000       |
| Municipalités  | 5 (MVP) | ~2,500       |
| **Total MVP**  | **27**  | **~80,000**  |

**Extension future**: ~5000 municipalités = +500,000 documents

## Calendrier de Mise à Jour

| Source Type    | Fréquence | Jour/Heure       |
|----------------|-----------|------------------|
| Justice Laws   | Quotidien | 02:00 EST        |
| Canada Gazette | Mercredi  | 10:00 EST        |
| SCC            | Variable  | Vérif quotidien  |
| Provinces      | Quotidien | 03:00-06:00 EST  |
| Municipalités  | Hebdo     | Dimanche 01:00   |

## Prochaines Sources (Roadmap)

### Q1 2026
- Cours d'appel fédérales
- Tribunaux administratifs fédéraux
- 50 municipalités moyennes

### Q2 2026
- Cours provinciales (Ontario, Québec, BC)
- 200 municipalités supplémentaires

### Q3-Q4 2026
- Extension complète 5000+ municipalités
- Tribunaux spécialisés
- Archives historiques

## Contact et Contributions

Pour suggérer l'ajout d'une nouvelle source:
- Email: admin@zeroobstacle.ca
- GitHub Issue: avec template "Nouvelle source"
- Informations requises: URL, licence, format, estimé docs
