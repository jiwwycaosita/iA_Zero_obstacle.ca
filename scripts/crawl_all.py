"""Crawler toutes les sources"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.firecrawl_crawler import crawl_multiple
from agents.sources_canada import get_all_sources

if __name__ == "__main__":
    print("🌐 Crawling de TOUTES les sources...")
    all_sources = get_all_sources()
    
    all_urls = []
    for category, content in all_sources.items():
        if isinstance(content, dict):
            for urls in content.values():
                all_urls.extend(urls)
        else:
            all_urls.extend(content)
    
    print(f"📊 Total: {len(all_urls)} URLs à crawler")
    results = crawl_multiple(all_urls)
    
    success = sum(1 for r in results if r["status"] == "success")
    print(f"\n✅ Succès: {success}/{len(results)}")
