"""
Unit tests for document normalizer
Tests PDF/HTML/XML extraction and metadata processing
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from src.normalizer import DocumentNormalizer


@pytest.fixture
def normalizer():
    """Create normalizer instance"""
    return DocumentNormalizer()


@pytest.fixture
def mock_html_document():
    """Mock HTML document"""
    return {
        'source': 'Test Source',
        'url': 'https://example.com/test.html',
        'title': 'Test Act',
        'type': 'html',
        'language': 'en',
        'category': 'federal',
        'document_type': 'act',
        'scraped_at': datetime.utcnow().timestamp()
    }


@pytest.fixture
def mock_pdf_document():
    """Mock PDF document"""
    return {
        'source': 'Test Source',
        'url': 'https://example.com/test.pdf',
        'title': 'Test Regulation',
        'type': 'pdf',
        'language': 'en',
        'category': 'provincial',
        'document_type': 'regulation',
        'scraped_at': datetime.utcnow().timestamp()
    }


class TestDocumentNormalizer:
    """Test DocumentNormalizer functionality"""
    
    @pytest.mark.asyncio
    async def test_normalize_html_document(self, normalizer, mock_html_document):
        """Test normalization of HTML document"""
        result = await normalizer.normalize(mock_html_document)
        
        # Check required fields
        assert 'id' in result
        assert 'content' in result
        assert 'content_hash' in result
        assert 'metadata' in result
        assert 'normalized_at' in result
        
        # Check metadata preservation
        assert result['source'] == mock_html_document['source']
        assert result['url'] == mock_html_document['url']
        assert result['title'] == mock_html_document['title']
        assert result['language'] == mock_html_document['language']
        
    @pytest.mark.asyncio
    async def test_normalize_pdf_document(self, normalizer, mock_pdf_document):
        """Test normalization of PDF document"""
        result = await normalizer.normalize(mock_pdf_document)
        
        # Should handle PDF type
        assert result['id'] is not None
        assert result['content'] is not None
        
    @pytest.mark.asyncio
    async def test_content_hash_generation(self, normalizer, mock_html_document):
        """Test content hash is generated correctly"""
        result1 = await normalizer.normalize(mock_html_document)
        result2 = await normalizer.normalize(mock_html_document)
        
        # Same content should produce same hash
        assert result1['content_hash'] == result2['content_hash']
        
    def test_generate_hash(self, normalizer):
        """Test hash generation"""
        content1 = "This is test content"
        content2 = "This is test content"
        content3 = "This is different content"
        
        hash1 = normalizer._generate_hash(content1)
        hash2 = normalizer._generate_hash(content2)
        hash3 = normalizer._generate_hash(content3)
        
        # Same content = same hash
        assert hash1 == hash2
        
        # Different content = different hash
        assert hash1 != hash3
        
        # Hash should be hex string
        assert len(hash1) == 64  # SHA-256 produces 64 hex chars
        
    def test_clean_text(self, normalizer):
        """Test text cleaning"""
        dirty_text = "  This   has  \n\n\n  extra    whitespace  \n\n  "
        clean = normalizer._clean_text(dirty_text)
        
        # Should remove extra whitespace
        assert "  " not in clean
        assert "\n\n\n" not in clean
        assert clean.startswith("This")
        assert clean.endswith("whitespace")
        
    def test_extract_metadata_from_content(self, normalizer):
        """Test metadata extraction from content"""
        document = {
            'title': 'Test Act',
            'url': 'https://example.com',
            'source': 'Test',
            'category': 'federal',
            'language': 'en'
        }
        
        content = """
        This is section 10 of the Act.
        Reference to S.C. 2024, c. 15.
        Date: 2024-01-15
        This is section 25 of the Act.
        """
        
        metadata = normalizer._extract_metadata(document, content)
        
        # Should extract sections
        assert 'sections' in metadata
        assert '10' in metadata['sections']
        assert '25' in metadata['sections']
        
        # Should extract dates
        assert 'dates_mentioned' in metadata
        
        # Should extract act references
        assert 'act_references' in metadata
        
    @pytest.mark.asyncio
    async def test_create_diff(self, normalizer):
        """Test diff creation between versions"""
        old_doc = {
            'content': 'Old content',
            'content_hash': 'hash1',
            'version': 1
        }
        
        new_doc = {
            'content': 'New content',
            'content_hash': 'hash2',
            'version': 2
        }
        
        diff = await normalizer.create_diff(old_doc, new_doc)
        
        # Should detect change
        assert diff['changed'] is True
        assert diff['old_hash'] == 'hash1'
        assert diff['new_hash'] == 'hash2'
        assert diff['old_version'] == 1
        assert diff['new_version'] == 2
        
    @pytest.mark.asyncio
    async def test_create_diff_no_change(self, normalizer):
        """Test diff when content unchanged"""
        doc1 = {
            'content': 'Same content',
            'content_hash': 'same_hash',
            'version': 1
        }
        
        doc2 = {
            'content': 'Same content',
            'content_hash': 'same_hash',
            'version': 1
        }
        
        diff = await normalizer.create_diff(doc1, doc2)
        
        # Should detect no change
        assert diff['changed'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
