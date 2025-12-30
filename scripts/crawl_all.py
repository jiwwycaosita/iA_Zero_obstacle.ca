"""Crawler toutes les sources"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.firecrawl_crawler import crawl_multiple
from agents.sources_canada import get_all_sources, flatten_all_urls

if __name__ == "__main__":
    print("🌐 Crawling de TOUTES les sources...")
    all_sources = get_all_sources()
    all_urls = flatten_all_urls(all_sources)
    
    print(f"📊 Total: {len(all_urls)} URLs à crawler")
    results = crawl_multiple(all_urls)
    
    success = sum(1 for r in results if r["status"] == "success")
    print(f"\n✅ Succès: {success}/{len(results)}")
