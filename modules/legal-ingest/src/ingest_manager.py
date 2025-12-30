"""
Legal Ingest Manager - Main Orchestrator
Coordinates scraping, normalization, and storage of legal documents
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv
from prometheus_client import Counter, Gauge, Histogram, start_http_server

from .scrapers import ScraperFactory
from .normalizer import DocumentNormalizer
from .embeddings import EmbeddingsPipeline

# Load environment variables
load_dotenv()

# Configure structured logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("legal_ingest.log")
    ]
)
logger = logging.getLogger(__name__)

# Prometheus metrics
DOCUMENTS_PROCESSED = Counter('documents_processed_total', 'Total documents processed', ['source', 'status'])
SCRAPING_DURATION = Histogram('scraping_duration_seconds', 'Time spent scraping', ['source'])
ACTIVE_SCRAPERS = Gauge('active_scrapers', 'Number of active scrapers')
QUEUE_SIZE = Gauge('queue_size', 'Number of documents in queue')


class IngestManager:
    """
    Main orchestrator for legal document ingestion pipeline
    Manages scrapers, normalization, and storage in daemon mode
    """
    
    def __init__(self, sources_config_path: str = "src/sources.yaml"):
        """Initialize the ingest manager with source configuration"""
        self.sources_config_path = Path(sources_config_path)
        self.sources = self._load_sources()
        self.scraper_factory = ScraperFactory()
        self.normalizer = DocumentNormalizer()
        self.embeddings_pipeline = EmbeddingsPipeline()
        self.running = False
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        
        logger.info(f"IngestManager initialized with {len(self.sources)} source categories")
        
    def _load_sources(self) -> Dict:
        """Load sources configuration from YAML file"""
        try:
            with open(self.sources_config_path, 'r', encoding='utf-8') as f:
                sources = yaml.safe_load(f)
                logger.info(f"Loaded sources configuration from {self.sources_config_path}")
                return sources
        except Exception as e:
            logger.error(f"Failed to load sources configuration: {e}")
            raise
            
    def _get_all_sources(self) -> List[Dict]:
        """Flatten all sources into a single list with metadata"""
        all_sources = []
        
        # Federal sources
        for source in self.sources.get('federal', []):
            source['category'] = 'federal'
            all_sources.append(source)
            
        # Provincial sources
        provinces = self.sources.get('provinces', {})
        for province, sources in provinces.items():
            for source in sources:
                source['category'] = 'provincial'
                source['province'] = province
                all_sources.append(source)
                
        # Regulators
        for source in self.sources.get('regulators', []):
            source['category'] = 'regulator'
            all_sources.append(source)
            
        # Municipalities
        municipalities = self.sources.get('municipalities', {})
        for city_type, cities in municipalities.items():
            for source in cities:
                source['category'] = 'municipal'
                source['city_type'] = city_type
                all_sources.append(source)
                
        # Sort by priority
        all_sources.sort(key=lambda x: x.get('priority', 999))
        
        return all_sources
        
    async def process_source(self, source: Dict) -> None:
        """
        Process a single source: scrape, normalize, store
        
        Args:
            source: Source configuration dictionary
        """
        source_name = source['name']
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                logger.info(f"Processing source: {source_name} (attempt {retry_count + 1}/{self.max_retries})")
                ACTIVE_SCRAPERS.inc()
                
                with SCRAPING_DURATION.labels(source=source_name).time():
                    # Create scraper for this source
                    scraper = self.scraper_factory.create_scraper(source)
                    
                    # Scrape documents
                    documents = await scraper.scrape()
                    logger.info(f"Scraped {len(documents)} documents from {source_name}")
                    
                    # Normalize each document
                    for doc in documents:
                        try:
                            normalized = await self.normalizer.normalize(doc)
                            
                            # Generate embeddings
                            embedded = await self.embeddings_pipeline.process(normalized)
                            
                            # TODO: Store in OpenSearch, Milvus, and Postgres
                            
                            DOCUMENTS_PROCESSED.labels(source=source_name, status='success').inc()
                            
                        except Exception as e:
                            logger.error(f"Failed to process document from {source_name}: {e}")
                            DOCUMENTS_PROCESSED.labels(source=source_name, status='error').inc()
                            
                ACTIVE_SCRAPERS.dec()
                break  # Success, exit retry loop
                
            except Exception as e:
                logger.error(f"Failed to process source {source_name}: {e}")
                retry_count += 1
                
                if retry_count < self.max_retries:
                    # Exponential backoff
                    wait_time = 2 ** retry_count
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Max retries reached for {source_name}")
                    DOCUMENTS_PROCESSED.labels(source=source_name, status='failed').inc()
                    ACTIVE_SCRAPERS.dec()
                    
    async def run_once(self) -> None:
        """Run ingestion pipeline once for all sources"""
        logger.info("Starting ingestion run")
        start_time = time.time()
        
        sources = self._get_all_sources()
        logger.info(f"Processing {len(sources)} sources")
        
        # Process sources in priority order
        # TODO: Implement parallel processing with concurrency limits
        for source in sources:
            await self.process_source(source)
            
        duration = time.time() - start_time
        logger.info(f"Ingestion run completed in {duration:.2f} seconds")
        
    async def run_daemon(self, interval_hours: int = 24) -> None:
        """
        Run ingestion pipeline in daemon mode (24/7)
        
        Args:
            interval_hours: Hours between ingestion runs
        """
        self.running = True
        logger.info(f"Starting daemon mode with {interval_hours}h interval")
        
        while self.running:
            try:
                await self.run_once()
                
                # Wait for next run
                logger.info(f"Waiting {interval_hours} hours until next run...")
                await asyncio.sleep(interval_hours * 3600)
                
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.running = False
            except Exception as e:
                logger.error(f"Error in daemon loop: {e}")
                # Wait before retrying
                await asyncio.sleep(300)  # 5 minutes
                
        logger.info("Daemon stopped")
        
    def stop(self) -> None:
        """Stop the daemon"""
        self.running = False
        

def main():
    """Main entry point for the ingestion manager"""
    # Start Prometheus metrics server
    metrics_port = int(os.getenv("PROMETHEUS_PORT", "9090"))
    start_http_server(metrics_port)
    logger.info(f"Prometheus metrics available at http://localhost:{metrics_port}")
    
    # Create and start manager
    manager = IngestManager()
    
    # Run in daemon mode
    try:
        asyncio.run(manager.run_daemon())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        manager.stop()
        

if __name__ == "__main__":
    main()
