"""
Unit tests for legal document scrapers
Tests HTTP scraping, robots.txt compliance, and source-specific connectors
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch

from src.scrapers import (
    BaseScraper,
    HTMLScraper,
    JusticeLawsScraper,
    CanadaGazetteScraper,
    SupremeCourtScraper,
    ScraperFactory
)


@pytest.fixture
def mock_source_config():
    """Mock source configuration"""
    return {
        'name': 'Test Source',
        'url': 'https://example.com',
        'type': 'html',
        'priority': 1,
        'languages': ['en'],
        'respect_robots': True,
        'rate_limit_seconds': 1
    }


@pytest.fixture
def mock_httpx_response():
    """Mock httpx response"""
    response = Mock()
    response.text = """
    <html>
        <body>
            <a href="/act/test-act.html">Test Act</a>
            <a href="/regulation/test-reg.pdf">Test Regulation</a>
        </body>
    </html>
    """
    response.raise_for_status = Mock()
    return response


class TestBaseScraper:
    """Test BaseScraper functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, mock_source_config):
        """Test that rate limiting works"""
        import time
        
        class TestScraper(BaseScraper):
            async def scrape(self):
                return []
        
        scraper = TestScraper(mock_source_config)
        
        # Make two requests and measure time
        start = time.time()
        await scraper._rate_limit_wait()
        await scraper._rate_limit_wait()
        elapsed = time.time() - start
        
        # Should take at least 1 second (rate limit)
        assert elapsed >= 1.0
        
    def test_robots_txt_check(self, mock_source_config):
        """Test robots.txt parsing"""
        class TestScraper(BaseScraper):
            async def scrape(self):
                return []
        
        scraper = TestScraper(mock_source_config)
        
        # Should be able to check if URL is allowed
        # (actual robots.txt may not be available in test)
        result = scraper._can_fetch(mock_source_config['url'])
        assert isinstance(result, bool)


class TestHTMLScraper:
    """Test HTMLScraper functionality"""
    
    @pytest.mark.asyncio
    async def test_scrape_finds_documents(self, mock_source_config, mock_httpx_response):
        """Test that HTML scraper finds document links"""
        scraper = HTMLScraper(mock_source_config)
        
        with patch.object(scraper, '_fetch_url', return_value=mock_httpx_response):
            documents = await scraper.scrape()
            
            # Should find at least one document
            assert len(documents) > 0
            
            # Check document structure
            doc = documents[0]
            assert 'source' in doc
            assert 'url' in doc
            assert 'title' in doc
            assert 'type' in doc
            
    @pytest.mark.asyncio
    async def test_scrape_handles_no_response(self, mock_source_config):
        """Test scraper handles failed requests"""
        scraper = HTMLScraper(mock_source_config)
        
        with patch.object(scraper, '_fetch_url', return_value=None):
            documents = await scraper.scrape()
            
            # Should return empty list on failure
            assert documents == []


class TestJusticeLawsScraper:
    """Test Justice Laws Canada scraper"""
    
    @pytest.mark.asyncio
    async def test_scrape_structure(self, mock_source_config):
        """Test Justice Laws scraper returns correct structure"""
        config = mock_source_config.copy()
        config['name'] = 'Justice Laws'
        
        scraper = JusticeLawsScraper(config)
        
        # Mock response
        mock_response = Mock()
        mock_response.text = """
        <html>
            <body>
                <a href="/eng/acts/A-1/index.html">Access to Information Act</a>
                <a href="/eng/acts/C-46/index.html">Criminal Code</a>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        
        with patch.object(scraper, '_fetch_url', return_value=mock_response):
            documents = await scraper.scrape()
            
            # Should find acts
            assert len(documents) > 0
            
            # Check metadata
            for doc in documents:
                assert doc['category'] == 'federal'
                assert doc['document_type'] == 'act'
                assert doc['jurisdiction'] == 'Canada (Federal)'


class TestCanadaGazetteScraper:
    """Test Canada Gazette RSS scraper"""
    
    @pytest.mark.asyncio
    async def test_parse_rss(self, mock_source_config):
        """Test RSS feed parsing"""
        config = mock_source_config.copy()
        config['name'] = 'Canada Gazette'
        
        scraper = CanadaGazetteScraper(config)
        
        # Mock RSS response
        mock_response = Mock()
        mock_response.text = """
        <?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test Gazette Entry</title>
                    <link>https://gazette.gc.ca/test</link>
                    <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
                    <description>Test description</description>
                </item>
            </channel>
        </rss>
        """
        mock_response.raise_for_status = Mock()
        
        with patch.object(scraper, '_fetch_url', return_value=mock_response):
            documents = await scraper.scrape()
            
            # Should find gazette entries
            assert len(documents) > 0
            
            # Check structure
            doc = documents[0]
            assert doc['document_type'] == 'gazette'
            assert 'publication_date' in doc


class TestScraperFactory:
    """Test ScraperFactory"""
    
    def test_create_specialized_scraper(self, mock_source_config):
        """Test factory creates specialized scrapers"""
        factory = ScraperFactory()
        
        # Test Justice Laws
        config = mock_source_config.copy()
        config['name'] = 'Justice Laws'
        scraper = factory.create_scraper(config)
        assert isinstance(scraper, JusticeLawsScraper)
        
        # Test Canada Gazette
        config['name'] = 'Canada Gazette'
        scraper = factory.create_scraper(config)
        assert isinstance(scraper, CanadaGazetteScraper)
        
        # Test Supreme Court
        config['name'] = 'Supreme Court of Canada'
        scraper = factory.create_scraper(config)
        assert isinstance(scraper, SupremeCourtScraper)
        
    def test_create_generic_scraper(self, mock_source_config):
        """Test factory creates generic scraper for unknown sources"""
        factory = ScraperFactory()
        
        config = mock_source_config.copy()
        config['name'] = 'Unknown Source'
        scraper = factory.create_scraper(config)
        
        # Should fall back to HTMLScraper
        assert isinstance(scraper, HTMLScraper)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
