import pytest
import json
from pathlib import Path
from agents.normalization import normalize_crawled_data

def test_normalization_structure():
    """Test que la normalisation produit la bonne structure"""
    # Créer un fichier test
    test_data = {
        "metadata": {
            "url": "https://test.com",
            "url_hash": "testhash123",
            "timestamp": "20250115_100000",
            "format": "markdown",
            "extraction_date": "2025-01-15T10:00:00"
        },
        "content": "Test content"
    }
    
    test_file = Path("data/can_gov/test_normalize.json")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text(json.dumps(test_data))
    
    # Normaliser
    result = normalize_crawled_data(test_file)
    
    # Vérifier la structure
    assert "source_url" in result
    assert "content_hash" in result
    assert "extraction_date" in result
    assert "processing_date" in result
    assert result["version"] == "1.0"
    
    # Cleanup
    test_file.unlink()
