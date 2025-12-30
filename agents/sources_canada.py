"""
Mapping complet des sources officielles canadiennes à crawler
"""

SOURCES_FEDERALES = {
    "prestations": [
        "https://www.canada.ca/fr/services/prestations.html",
        "https://www.canada.ca/en/services/benefits.html",
        "https://www.canada.ca/fr/services/prestations/ae.html",  # Assurance-emploi
        "https://www.canada.ca/fr/services/prestations/pensionspubliques.html",  # Pensions
        "https://www.canada.ca/fr/services/prestations/famille.html",  # Allocations familiales
        "https://www.canada.ca/fr/services/prestations/invalidite.html",  # Invalidité
    ],
    "impots": [
        "https://www.canada.ca/fr/agence-revenu/services/impot.html",
        "https://www.canada.ca/fr/agence-revenu/services/prestations-enfants-familles.html",
        "https://www.canada.ca/fr/agence-revenu/services/prestations-enfants-familles/allocation-canadienne-enfants-apercu.html",
    ],
    "immigration": [
        "https://www.canada.ca/fr/services/immigration-citoyennete.html",
        "https://www.canada.ca/fr/immigration-refugies-citoyennete/services/immigrer-canada.html",
    ],
    "emploi": [
        "https://www.canada.ca/fr/services/emplois.html",
        "https://www.guichetemplois.gc.ca/accueil",
    ],
    "logement": [
        "https://www.canada.ca/fr/services/finances/gerer-argent-budget/aide-financiere-logement.html",
    ],
    "sante": [
        "https://www.canada.ca/fr/sante-publique.html",
    ],
    "open_data": [
        "https://open.canada.ca/data/fr/dataset",
        "https://open.canada.ca/fr/donnees-ouvertes",
    ]
}

SOURCES_QUEBEC = {
    "prestations": [
        "https://www.quebec.ca/famille-et-soutien-aux-personnes/aide-financiere",
        "https://www.quebec.ca/emploi/aide-financiere-emploi",
    ],
    "impots": [
        "https://www.revenuquebec.ca/fr/",
        "https://www.revenuquebec.ca/fr/citoyens/",
    ],
    "sante": [
        "https://www.quebec.ca/sante",
        "https://www.ramq.gouv.qc.ca/fr",
    ],
    "education": [
        "https://www.quebec.ca/education/aide-financiere-aux-etudes",
    ]
}

SOURCES_ONTARIO = {
    "prestations": [
        "https://www.ontario.ca/fr/page/services-sociaux-et-communautaires",
    ],
    "sante": [
        "https://www.ontario.ca/fr/page/soins-de-sante-en-ontario",
    ]
}

SOURCES_PDF_FEDERALES = [
    "https://www.canada.ca/content/dam/canada/employment-social-development/migration/documents/assets/portfolio/docs/fr/ae/ae-digest/ae_digest_2023.pdf",
    # Ajouter autres PDFs de formulaires officiels
]


def get_all_sources() -> dict:
    """Retourne toutes les sources organisées par type"""
    return {
        "federal": SOURCES_FEDERALES,
        "quebec": SOURCES_QUEBEC,
        "ontario": SOURCES_ONTARIO,
        "pdfs": SOURCES_PDF_FEDERALES
    }


def get_priority_sources() -> list:
    """Retourne les sources prioritaires pour MVP"""
    return [
        # Federal - Prestations essentielles
        "https://www.canada.ca/fr/services/prestations.html",
        "https://www.canada.ca/fr/services/prestations/ae.html",
        "https://www.canada.ca/fr/agence-revenu/services/prestations-enfants-familles/allocation-canadienne-enfants-apercu.html",
        
        # Quebec - Top 3
        "https://www.quebec.ca/famille-et-soutien-aux-personnes/aide-financiere",
        "https://www.revenuquebec.ca/fr/citoyens/",
        
        # Open Data
        "https://open.canada.ca/data/fr/dataset",
    ]


if __name__ == "__main__":
    sources = get_all_sources()
    print(f"📚 Total des sources: {sum(len(v) if isinstance(v, list) else sum(len(vv) for vv in v.values()) for v in sources.values())}")
    
    for category, urls in sources.items():
        if isinstance(urls, dict):
            for sub, sub_urls in urls.items():
                print(f"\n{category.upper()} - {sub}: {len(sub_urls)} URLs")
        else:
            print(f"\n{category.upper()}: {len(urls)} URLs")
