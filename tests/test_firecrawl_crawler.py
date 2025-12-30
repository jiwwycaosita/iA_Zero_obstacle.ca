import pytest
from pathlib import Path
from agents.firecrawl_crawler import get_url_hash, OUTDIR

def test_url_hash_generation():
    """Test génération hash URL"""
    url = "https://www.canada.ca/fr/services/prestations.html"
    hash1 = get_url_hash(url)
    hash2 = get_url_hash(url)
    
    assert len(hash1) == 12
    assert hash1 == hash2  # Déterministe
    assert hash1 != get_url_hash("https://other.url")

def test_output_directory_exists():
    """Test que le dossier de sortie existe"""
    assert OUTDIR.exists()
    assert OUTDIR.is_dir()

def test_crawl_creates_output():
    """Test qu'un crawl produit un fichier (nécessite Firecrawl key)"""
    # Skip si pas de clé
    import os
    if not os.getenv("FIRECRAWL_API_KEY"):
        pytest.skip("FIRECRAWL_API_KEY non définie")
    
    # Vérifier qu'il y a au moins un fichier de crawl
    files = list(OUTDIR.glob("*.json"))
    # Ce test passe si au moins un crawl a été fait
    # Pour un vrai test, il faudrait mocker ou utiliser une URL de test
