# Conformité Légale - Legal Ingest Pipeline

## Introduction

Ce document établit le cadre juridique et les obligations de conformité pour l'ingestion, le stockage et la diffusion des contenus légaux canadiens dans le cadre du projet Zéro Obstacle.

## Autorisation officielle

**Approbation signée**: `legal_approval_signed.txt`

```
Signataire: Jimmy Renaud
Date: 2025-12-30
Portée: Usage commercial autorisé
Juridictions: Fédéral, provinces, municipalités, régulateurs
```

## Sources et licences

### 1. Sources gouvernementales fédérales

#### Justice Laws (lois.justice.gc.ca)

- **Licence**: Licence du gouvernement ouvert - Canada
- **URL**: https://open.canada.ca/fr/licence-du-gouvernement-ouvert-canada
- **Permissions**:
  - ✅ Copie, modification, distribution
  - ✅ Usage commercial autorisé
  - ✅ Adaptation et traduction
- **Obligations**:
  - Attribution à la source
  - Lien vers la licence
  - Mention des modifications
- **Restrictions**:
  - ❌ Pas de suggestion d'approbation officielle
  - ❌ Respect droits tiers (marques, brevets)

#### Canada Gazette

- **Licence**: Licence du gouvernement ouvert - Canada
- **Permissions**: Identiques à Justice Laws
- **Note**: Publication officielle du gouvernement du Canada

#### Supreme Court of Canada

- **Licence**: Licence du gouvernement ouvert - Canada
- **Permissions**: Identiques
- **Attribution requise**: "Cour suprême du Canada"

### 2. CanLII (Institut canadien d'information juridique)

- **Statut**: Organisation à but non lucratif
- **Licence**: Creative Commons BY-NC-SA 4.0 pour certains contenus
- **URL**: https://www.canlii.org/en/info/terms.html
- **Permissions**:
  - ✅ Usage non commercial (gratuit)
  - ⚠️ Usage commercial requiert négociation
- **Actions requises**:
  - Contacter CanLII pour accord bulk download
  - Négocier licence commerciale si applicable
  - Utiliser API avec clé si fournie
- **Attribution**: "Source: CanLII (www.canlii.org)"

### 3. Sources provinciales

#### Ontario (ontario.ca/laws)

- **Licence**: Licence du gouvernement ouvert - Ontario
- **URL**: https://www.ontario.ca/fr/page/licence-du-gouvernement-ouvert-ontario
- **Permissions**: Usage commercial autorisé
- **Attribution**: "Source: Gouvernement de l'Ontario"

#### Québec (legisquebec.gouv.qc.ca)

- **Licence**: Licence libre du Québec (LiLiQ-P)
- **URL**: https://forge.gouv.qc.ca/licence/liliq-v1-1/
- **Permissions**: Usage commercial autorisé
- **Attribution**: "Source: Publications du Québec"

#### British Columbia (bclaws.gov.bc.ca)

- **Licence**: Open Government Licence - British Columbia
- **Permissions**: Usage commercial autorisé
- **Attribution**: "Source: Province of British Columbia"

#### Autres provinces

- Même cadre général: licences ouvertes gouvernementales
- Vérification individuelle nécessaire
- Attribution à la source obligatoire

### 4. Municipalités

- **Statut**: Variable selon municipalité
- **Présomption**: Documents publics utilisables
- **Prudence**: Vérifier terms of use de chaque site
- **Attribution**: Nom de la ville source
- **Note**: Peut nécessiter contact pour clarification

### 5. Régulateurs (CRA, AMF, IRCC, etc.)

- **Licence**: Généralement gouvernement ouvert
- **Permissions**: Usage commercial autorisé
- **Attribution**: Nom de l'organisme
- **Cas spécial AMF**: Vérifier conditions Québec

## Conformité RGPD / Loi 25 (Québec)

### Applicabilité

- **RGPD**: Non applicable (données publiques, pas de citoyens UE)
- **Loi 25**: Applicable (Québec)

### Données traitées

- ✅ **Contenus légaux publics**: OK, pas de données personnelles
- ⚠️ **Métadonnées scraping**: IP, timestamps → minimiser
- ❌ **Pas de collecte utilisateurs** pour MVP

### Mesures de conformité

1. **Minimisation**: Collecter seulement données nécessaires
2. **Transparence**: Politique de confidentialité sur site
3. **Sécurité**: Chiffrement, accès contrôlé, backups
4. **Conservation**: Politique de rétention claire
5. **Droits**: Mécanisme pour demandes d'accès/rectification

## Hébergement au Canada

### Exigences

- ✅ **PlanetHoster**: Hébergement Canada confirmé
- ✅ **Serveurs locaux**: Physiquement au Canada
- ✅ **Backups**: Stockage local Canada

### Raisons

1. **Souveraineté des données**: Lois canadiennes
2. **Performance**: Latence réduite pour utilisateurs canadiens
3. **Confiance**: Données sensibles restent au Canada
4. **Conformité**: Certains règlements l'exigent

## Respect robots.txt et terms of service

### Implémentation

```python
# Voir src/scrapers.py
- Lecture robots.txt obligatoire
- Respect User-Agent: ZeroObstacle-LegalIngest/1.0
- Rate limiting: 2-5 secondes entre requêtes
- Respect crawl-delay si spécifié
```

### Monitoring

- Logs de conformité robots.txt
- Alertes si blocage détecté
- Processus d'escalade si problème

## Attribution et mentions légales

### Page "À propos" requise

```markdown
# Sources de données

Ce service utilise des données provenant de:

**Fédéral**
- Justice Laws (lois.justice.gc.ca)
  Licence: Gouvernement ouvert - Canada
  
- Canada Gazette (gazette.gc.ca)
  Licence: Gouvernement ouvert - Canada
  
**Provincial**
- Ontario e-Laws (ontario.ca/laws)
  Licence: Gouvernement ouvert - Ontario
  
[... liste complète ...]

**Attribution générale**
Contient des informations reproduites avec la permission 
du gouvernement du Canada et des provinces participantes.

**Disclaimer**
Les contenus sont fournis à titre informatif. Consulter 
les sources officielles pour version faisant foi.
```

### Footer site web

```
© 2025 Zéro Obstacle | Données: Gouvernement du Canada et provinces
Licence: Voir page Attribution | Non affilié aux gouvernements
```

## Propriété intellectuelle

### Contenus légaux

- **Statut**: Domaine public (Crown Copyright limité)
- **Base légale**: Reproduction autorisée par licences ouvertes
- **Modifications**: Autorisées avec attribution
- **Droit moral**: Respecté (pas de déformation)

### Traductions

- **Originaux FR/EN**: Utilisables tels quels
- **Nouvelles traductions**: Possibles avec attribution
- **Qualité**: Responsabilité de Zéro Obstacle

### Marques

- ❌ Ne pas suggérer approbation gouvernementale
- ❌ Ne pas utiliser armoiries/logos officiels sans permission
- ✅ Mentionner sources textuellement

## Responsabilité et disclaimers

### Disclaimer obligatoire

```
AVIS IMPORTANT

Les contenus juridiques présentés sur ce site sont fournis 
à titre informatif seulement et ne constituent pas des 
conseils juridiques.

- Les textes peuvent ne pas refléter les dernières 
  modifications législatives.
- Consulter toujours les versions officielles publiées 
  par les gouvernements.
- Zéro Obstacle n'est pas responsable des erreurs, 
  omissions ou interprétations.
- Pour des conseils juridiques, consulter un avocat 
  ou notaire qualifié.

Sources officielles:
- Fédéral: laws-lois.justice.gc.ca
- Ontario: ontario.ca/laws
- Québec: legisquebec.gouv.qc.ca
[...]
```

### Limitation de responsabilité

- Pas de garantie d'exactitude
- Pas de garantie de complétude
- Pas de responsabilité pour dommages
- Usage aux risques de l'utilisateur

## Versioning et traçabilité

### Obligations

1. **Horodatage**: Date de capture source
2. **Versioning**: Historique des modifications
3. **Provenance**: URL source + date
4. **Modifications**: Log de tous changements

### Implémentation

```python
# Voir src/normalizer.py
metadata = {
    'source_url': 'https://...',
    'scraped_at': '2025-12-30T12:00:00Z',
    'version': 1,
    'content_hash': 'sha256...',
    'modifications': []
}
```

## Négociations en cours

### CanLII

- **Statut**: À négocier
- **Objectif**: Accord bulk download
- **Licence commerciale**: À discuter
- **Contact**: Via formulaire CanLII
- **Timeline**: Q1 2026

### Provinces (bulk)

- **Objectif**: Accès API ou dumps bulk
- **Bénéfice**: Réduction charge serveurs
- **Approche**: Contact officiel par province
- **Timeline**: Q2-Q3 2026

## Audit et conformité

### Audit annuel

- Revue licences sources
- Vérification attributions
- Test conformité robots.txt
- Validation hébergement Canada
- Revue disclaimers

### Documentation

- Registre licences sources (ce document)
- Logs conformité scraping
- Preuves hébergement Canada
- Copies licences applicables

### Responsable conformité

- **Nom**: Jimmy Renaud
- **Rôle**: Responsable légal et technique
- **Contact**: admin@zeroobstacle.ca
- **Révision**: Annuelle

## Procédure en cas de plainte

### Réception plainte

1. Accusé réception sous 48h
2. Suspension immédiate source concernée si demandé
3. Analyse juridique (interne + avocat si nécessaire)
4. Réponse motivée sous 7 jours ouvrables

### Résolution

- Modification/suppression contenu si justifié
- Négociation accord si applicable
- Documentation décision
- Suivi 30-60-90 jours

### Escalade

- Contact avocat spécialisé propriété intellectuelle
- Médiation si nécessaire
- Arbitrage en dernier recours

## Checklist de conformité

- [x] Approbation légale signée (legal_approval_signed.txt)
- [x] Licences sources documentées
- [x] Hébergement Canada confirmé
- [x] Respect robots.txt implémenté
- [x] Rate limiting configuré
- [x] Attribution sources dans code
- [ ] Page Attribution sur site web (à créer)
- [ ] Disclaimers affichés (à créer)
- [ ] Politique confidentialité (à créer)
- [ ] Contact CanLII initié (à faire)
- [ ] Tests conformité automatisés (à implémenter)

## Références légales

- [Licence du gouvernement ouvert - Canada](https://open.canada.ca/fr/licence-du-gouvernement-ouvert-canada)
- [Licence du gouvernement ouvert - Ontario](https://www.ontario.ca/fr/page/licence-du-gouvernement-ouvert-ontario)
- [Licence libre du Québec (LiLiQ)](https://forge.gouv.qc.ca/licence/liliq-v1-1/)
- [Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.fr)
- [Loi 25 - Protection des renseignements personnels (Québec)](https://www.quebec.ca/gouvernement/politiques-orientations/loi-25-protection-renseignements-personnels)

## Mise à jour

- **Version**: 1.0
- **Date**: 2025-12-30
- **Prochaine révision**: 2026-12-30
- **Responsable**: Jimmy Renaud
