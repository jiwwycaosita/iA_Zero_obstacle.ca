"""
Normalisation des données crawlées vers format unifié
"""
import json
from pathlib import Path
from datetime import datetime
import hashlib

PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def normalize_crawled_data(input_file: Path) -> dict:
    """
    Normalise un fichier JSON crawlé vers le format standard
    
    Format standard:
    {
        "source_url": str,
        "content_hash": str,
        "extraction_date": str,
        "processing_date": str,
        "format": str,
        "content": str,
        "metadata": dict
    }
    """
    data = json.loads(input_file.read_text())
    
    content = data.get("content", "")
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    
    normalized = {
        "source_url": data["metadata"]["url"],
        "content_hash": content_hash,
        "extraction_date": data["metadata"]["extraction_date"],
        "processing_date": datetime.now().isoformat(),
        "format": data["metadata"]["format"],
        "content": content,
        "metadata": data["metadata"],
        "version": "1.0"
    }
    
    # Nom de fichier normalisé
    url_hash = data["metadata"]["url_hash"]
    output_file = PROCESSED_DIR / f"normalized_{url_hash}.json"
    
    output_file.write_text(json.dumps(normalized, ensure_ascii=False, indent=2))
    
    return normalized


def normalize_all():
    """Normalise tous les fichiers crawlés non encore traités"""
    raw_dir = Path("data/can_gov")
    
    for raw_file in raw_dir.glob("*.json"):
        url_hash = raw_file.stem.split("_")[0]
        normalized_file = PROCESSED_DIR / f"normalized_{url_hash}.json"
        
        if not normalized_file.exists():
            print(f"📝 Normalizing: {raw_file.name}")
            normalize_crawled_data(raw_file)


if __name__ == "__main__":
    normalize_all()
    print("✅ Normalisation terminée")
