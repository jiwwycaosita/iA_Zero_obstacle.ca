"""Crawler les sources prioritaires"""
import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.firecrawl_crawler import crawl_multiple
from agents.sources_canada import get_priority_sources

if __name__ == "__main__":
    print("🎯 Crawling des sources prioritaires...")
    urls = get_priority_sources()
    results = crawl_multiple(urls)
    
    success = sum(1 for r in results if r["status"] == "success")
    print(f"\n✅ Succès: {success}/{len(results)}")
