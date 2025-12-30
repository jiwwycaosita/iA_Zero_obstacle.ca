"""
Module d'extraction via Firecrawl pour sources gouvernementales canadiennes
"""
import os
import subprocess
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
OUTDIR = Path("data/can_gov")
PROCESSED_DIR = Path("data/processed")
LOGS_DIR = Path("data/logs")

# Créer les dossiers
for dir_path in [OUTDIR, PROCESSED_DIR, LOGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def get_url_hash(url: str) -> str:
    """Générer un hash unique pour l'URL"""
    return hashlib.sha256(url.encode()).hexdigest()[:12]


def crawl_url(url: str, format: str = "markdown") -> dict:
    """
    Crawler une URL avec Firecrawl
    
    Args:
        url: URL à crawler
        format: Format de sortie (markdown, html, text)
    
    Returns:
        dict avec status, output_file, metadata
    """
    if not FIRECRAWL_API_KEY:
        raise ValueError("FIRECRAWL_API_KEY non définie dans .env")
    
    # Validate format parameter
    allowed_formats = ["markdown", "html", "text"]
    if format not in allowed_formats:
        raise ValueError(f"Format invalide: {format}. Formats permis: {allowed_formats}")
    
    # Basic URL validation
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"URL invalide: {url}. L'URL doit commencer par http:// ou https://")
    
    url_hash = get_url_hash(url)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nom de fichier basé sur URL + timestamp
    filename = f"{url_hash}_{timestamp}.json"
    outfile = OUTDIR / filename
    
    # Préparer l'environnement
    env = os.environ.copy()
    env["FIRECRAWL_API_KEY"] = FIRECRAWL_API_KEY
    
    # Commande Firecrawl
    command = [
        "npx", "-y", "@mendable/firecrawl-js",
        "scrape",
        url,
        "--format", format
    ]
    
    print(f"🔍 Crawling: {url}")
    print(f"📁 Output: {outfile}")
    
    try:
        result = subprocess.run(
            command,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or "Unknown error"
            print(f"❌ Erreur: {error_msg}")
            
            # Log l'erreur
            log_file = LOGS_DIR / f"error_{url_hash}_{timestamp}.log"
            log_file.write_text(f"URL: {url}\nError: {error_msg}\n")
            
            return {
                "status": "error",
                "url": url,
                "error": error_msg,
                "timestamp": timestamp
            }
        
        # Sauvegarder le résultat
        content = result.stdout
        
        metadata = {
            "url": url,
            "url_hash": url_hash,
            "timestamp": timestamp,
            "format": format,
            "size_bytes": len(content),
            "extraction_date": datetime.now().isoformat()
        }
        
        output_data = {
            "metadata": metadata,
            "content": content
        }
        
        outfile.write_text(json.dumps(output_data, ensure_ascii=False, indent=2))
        
        print(f"✅ Crawl réussi: {outfile}")
        
        return {
            "status": "success",
            "output_file": str(outfile),
            "metadata": metadata
        }
        
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout après 120s pour {url}")
        return {
            "status": "timeout",
            "url": url,
            "timestamp": timestamp
        }
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return {
            "status": "error",
            "url": url,
            "error": str(e),
            "timestamp": timestamp
        }


def crawl_multiple(urls: list, format: str = "markdown") -> list:
    """Crawler plusieurs URLs"""
    results = []
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing {url}")
        result = crawl_url(url, format)
        results.append(result)
    
    # Sauvegarder le rapport
    report_file = LOGS_DIR / f"crawl_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    
    print(f"\n📊 Rapport sauvegardé: {report_file}")
    
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agents/firecrawl_crawler.py <URL> [format]")
        print("Formats: markdown (défaut), html, text")
        sys.exit(1)
    
    url = sys.argv[1]
    format = sys.argv[2] if len(sys.argv) > 2 else "markdown"
    
    crawl_url(url, format)
