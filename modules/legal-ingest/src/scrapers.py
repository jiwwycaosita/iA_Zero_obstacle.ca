"""
Legal Document Scrapers
Connectors for various legal sources (Justice Laws, CanLII, provinces, etc.)
"""

import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all scrapers"""
    
    def __init__(self, source_config: Dict):
        """
        Initialize scraper with source configuration
        
        Args:
            source_config: Dictionary with source metadata
        """
        self.config = source_config
        self.name = source_config['name']
        self.url = source_config['url']
        self.rate_limit = source_config.get('rate_limit_seconds', 2)
        self.respect_robots = source_config.get('respect_robots', True)
        self.timeout = int(os.getenv("TIMEOUT", "30"))
        self.user_agent = os.getenv("USER_AGENT", "ZeroObstacle-LegalIngest/1.0")
        self.last_request_time = 0
        
        # Check robots.txt
        if self.respect_robots:
            self.robot_parser = self._check_robots_txt()
        else:
            self.robot_parser = None
            
    def _check_robots_txt(self) -> Optional[RobotFileParser]:
        """Check robots.txt for the source URL"""
        try:
            parsed_url = urlparse(self.url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            logger.info(f"Loaded robots.txt for {self.name}")
            return rp
        except Exception as e:
            logger.warning(f"Failed to load robots.txt for {self.name}: {e}")
            return None
            
    def _can_fetch(self, url: str) -> bool:
        """Check if we can fetch the URL according to robots.txt"""
        if not self.robot_parser:
            return True
        return self.robot_parser.can_fetch(self.user_agent, url)
        
    async def _rate_limit_wait(self) -> None:
        """Wait to respect rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            wait_time = self.rate_limit - elapsed
            await asyncio.sleep(wait_time)
        self.last_request_time = time.time()
        
    async def _fetch_url(self, url: str, **kwargs) -> Optional[httpx.Response]:
        """
        Fetch a URL with rate limiting and error handling
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for httpx
            
        Returns:
            Response object or None if failed
        """
        # Check robots.txt
        if not self._can_fetch(url):
            logger.warning(f"Blocked by robots.txt: {url}")
            return None
            
        # Rate limiting
        await self._rate_limit_wait()
        
        # Make request
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = kwargs.pop('headers', {})
                headers['User-Agent'] = self.user_agent
                
                response = await client.get(url, headers=headers, **kwargs)
                response.raise_for_status()
                
                logger.debug(f"Successfully fetched {url}")
                return response
                
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
            
    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Scrape documents from this source
        
        Returns:
            List of document dictionaries with metadata
        """
        pass
        

class HTMLScraper(BaseScraper):
    """Generic HTML scraper for legal websites"""
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape HTML documents"""
        documents = []
        
        response = await self._fetch_url(self.url)
        if not response:
            return documents
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Generic extraction - should be customized per source
        # Look for links to legal documents
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            if not href:
                continue
                
            # Build full URL
            full_url = urljoin(self.url, href)
            
            # Filter for likely legal documents
            if any(ext in href.lower() for ext in ['.pdf', '.html', '/act/', '/law/', '/regulation/']):
                doc = {
                    'source': self.name,
                    'url': full_url,
                    'title': link.get_text(strip=True),
                    'type': 'pdf' if '.pdf' in href.lower() else 'html',
                    'language': self.config.get('languages', ['en'])[0],
                    'category': self.config.get('category', 'unknown'),
                    'scraped_at': time.time()
                }
                documents.append(doc)
                
        logger.info(f"Found {len(documents)} documents from {self.name}")
        return documents[:100]  # Limit for MVP
        

class JusticeLawsScraper(HTMLScraper):
    """Specialized scraper for Justice Laws Canada"""
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape Justice Laws consolidated acts"""
        documents = []
        
        # Start with the acts index page
        index_url = "https://laws-lois.justice.gc.ca/eng/acts/"
        response = await self._fetch_url(index_url)
        
        if not response:
            return documents
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all act links
        act_links = soup.find_all('a', href=True)
        
        for link in act_links:
            href = link.get('href')
            if not href or '/eng/acts/' not in href:
                continue
                
            full_url = urljoin(index_url, href)
            title = link.get_text(strip=True)
            
            doc = {
                'source': self.name,
                'url': full_url,
                'title': title,
                'type': 'html',
                'language': 'en',
                'category': 'federal',
                'document_type': 'act',
                'jurisdiction': 'Canada (Federal)',
                'scraped_at': time.time()
            }
            documents.append(doc)
            
        logger.info(f"Found {len(documents)} acts from Justice Laws")
        return documents[:50]  # Limit for MVP
        

class CanadaGazetteScraper(BaseScraper):
    """Scraper for Canada Gazette (RSS feed)"""
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape Canada Gazette via RSS"""
        documents = []
        
        # RSS feed URL
        rss_url = "https://www.gazette.gc.ca/rss/gazette-eng.xml"
        response = await self._fetch_url(rss_url)
        
        if not response:
            return documents
            
        soup = BeautifulSoup(response.text, 'xml')
        items = soup.find_all('item')
        
        for item in items:
            title = item.find('title')
            link = item.find('link')
            pub_date = item.find('pubDate')
            description = item.find('description')
            
            if title and link:
                doc = {
                    'source': self.name,
                    'url': link.get_text(strip=True),
                    'title': title.get_text(strip=True),
                    'type': 'html',
                    'language': 'en',
                    'category': 'federal',
                    'document_type': 'gazette',
                    'publication_date': pub_date.get_text(strip=True) if pub_date else None,
                    'description': description.get_text(strip=True) if description else None,
                    'scraped_at': time.time()
                }
                documents.append(doc)
                
        logger.info(f"Found {len(documents)} gazette entries")
        return documents
        

class CanLIIScraper(BaseScraper):
    """Scraper for CanLII (Canadian Legal Information Institute)"""
    
    def __init__(self, source_config: Dict):
        super().__init__(source_config)
        self.api_key = os.getenv("CANLII_API_KEY")
        
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape CanLII via API or bulk download if available"""
        documents = []
        
        if self.api_key:
            # Use API
            logger.info("Using CanLII API")
            # TODO: Implement CanLII API integration
            # For now, return empty list as placeholder
        else:
            logger.warning("CanLII API key not provided, skipping")
            
        return documents
        

class SupremeCourtScraper(HTMLScraper):
    """Scraper for Supreme Court of Canada decisions"""
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape Supreme Court decisions"""
        documents = []
        
        # Judgments page
        judgments_url = "https://www.scc-csc.ca/case-dossier/index-eng.aspx"
        response = await self._fetch_url(judgments_url)
        
        if not response:
            return documents
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find judgment links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            if not href or 'case-dossier' not in href:
                continue
                
            full_url = urljoin(judgments_url, href)
            title = link.get_text(strip=True)
            
            doc = {
                'source': self.name,
                'url': full_url,
                'title': title,
                'type': 'html',
                'language': 'en',
                'category': 'federal',
                'document_type': 'judgment',
                'court': 'Supreme Court of Canada',
                'scraped_at': time.time()
            }
            documents.append(doc)
            
        logger.info(f"Found {len(documents)} Supreme Court decisions")
        return documents[:30]  # Limit for MVP
        

class ScraperFactory:
    """Factory to create appropriate scraper for each source"""
    
    # Map source names to specialized scrapers
    SCRAPER_MAP = {
        'Justice Laws': JusticeLawsScraper,
        'Canada Gazette': CanadaGazetteScraper,
        'CanLII': CanLIIScraper,
        'Supreme Court of Canada': SupremeCourtScraper,
    }
    
    def create_scraper(self, source_config: Dict) -> BaseScraper:
        """
        Create appropriate scraper for the source
        
        Args:
            source_config: Source configuration dictionary
            
        Returns:
            Scraper instance
        """
        source_name = source_config['name']
        scraper_class = self.SCRAPER_MAP.get(source_name, HTMLScraper)
        
        logger.debug(f"Creating {scraper_class.__name__} for {source_name}")
        return scraper_class(source_config)
