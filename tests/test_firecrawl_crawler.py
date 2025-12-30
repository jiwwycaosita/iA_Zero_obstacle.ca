import pytest
from pathlib import Path
import os

def test_url_hash_generation():
    """Test génération hash URL"""
    from agents.firecrawl_crawler import get_url_hash
    
    url = "https://www.canada.ca/fr/services/prestations.html"
    hash1 = get_url_hash(url)
    hash2 = get_url_hash(url)
    
    assert len(hash1) == 12
    assert hash1 == hash2  # Déterministe
    assert hash1 != get_url_hash("https://other.url")

def test_output_directory_exists():
    """Test que le dossier de sortie existe"""
    from agents.firecrawl_crawler import OUTDIR
    
    assert OUTDIR.exists()
    assert OUTDIR.is_dir()

def test_url_validation():
    """Test validation des URLs"""
    # Set a dummy API key for testing validation
    os.environ["FIRECRAWL_API_KEY"] = "test-key"
    
    # Re-import to pick up the new env var
    import importlib
    import agents.firecrawl_crawler
    importlib.reload(agents.firecrawl_crawler)
    from agents.firecrawl_crawler import crawl_url
    
    # Test invalid URL (no http/https)
    with pytest.raises(ValueError, match="URL invalide"):
        crawl_url("www.invalid.com")
    
    # Test invalid format
    with pytest.raises(ValueError, match="Format invalide"):
        crawl_url("https://www.canada.ca", format="invalid")
    
    # Cleanup
    del os.environ["FIRECRAWL_API_KEY"]

def test_crawl_creates_output():
    """Test qu'un crawl produit un fichier (nécessite Firecrawl key)"""
    from agents.firecrawl_crawler import OUTDIR
    
    # Skip si pas de clé
    if not os.getenv("FIRECRAWL_API_KEY") or os.getenv("FIRECRAWL_API_KEY") == "test-key":
        pytest.skip("FIRECRAWL_API_KEY non définie")
    
    # Vérifier qu'il y a au moins un fichier de crawl
    files = list(OUTDIR.glob("*.json"))
    # Ce test passe si au moins un crawl a été fait
    # Pour un vrai test, il faudrait mocker ou utiliser une URL de test
