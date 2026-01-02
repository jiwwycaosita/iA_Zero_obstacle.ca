"""
Document Normalizer
Converts PDF, HTML, XML to clean text and extracts metadata
"""

import hashlib
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

logger = logging.getLogger(__name__)


class DocumentNormalizer:
    """
    Normalizes documents from various formats to a canonical JSON structure
    with clean text, metadata, and versioning support
    """
    
    def __init__(self):
        """Initialize the normalizer"""
        if PdfReader is None:
            logger.warning("pypdf not installed, PDF extraction will be limited")
            
    async def normalize(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a document to canonical format
        
        Args:
            document: Raw document dictionary with 'url', 'type', etc.
            
        Returns:
            Normalized document with clean text and metadata
        """
        doc_type = document.get('type', 'html')
        
        # Extract content based on type
        if doc_type == 'pdf':
            content = await self._extract_pdf(document)
        elif doc_type == 'html':
            content = await self._extract_html(document)
        elif doc_type == 'xml':
            content = await self._extract_xml(document)
        else:
            logger.warning(f"Unknown document type: {doc_type}")
            content = ""
            
        # Extract metadata
        metadata = self._extract_metadata(document, content)
        
        # Generate content hash for deduplication
        content_hash = self._generate_hash(content)
        
        # Build normalized document
        normalized = {
            'id': content_hash,
            'source': document.get('source'),
            'url': document.get('url'),
            'title': metadata.get('title', document.get('title', 'Untitled')),
            'content': content,
            'content_hash': content_hash,
            'language': document.get('language', 'en'),
            'category': document.get('category'),
            'document_type': document.get('document_type'),
            'jurisdiction': metadata.get('jurisdiction', document.get('jurisdiction')),
            'metadata': metadata,
            'scraped_at': document.get('scraped_at'),
            'normalized_at': datetime.utcnow().isoformat(),
            'version': 1
        }
        
        logger.debug(f"Normalized document: {normalized['title']}")
        return normalized
        
    async def _extract_pdf(self, document: Dict[str, Any]) -> str:
        """
        Extract text from PDF document
        
        Args:
            document: Document dictionary with PDF data
            
        Returns:
            Extracted text
        """
        # TODO: Implement actual PDF fetching and extraction
        # For MVP, return placeholder
        logger.info(f"PDF extraction for {document.get('url')} (placeholder)")
        
        if PdfReader is None:
            return "[PDF extraction not available - pypdf not installed]"
            
        # In production:
        # 1. Fetch PDF from URL
        # 2. Use PdfReader to extract text
        # 3. If text extraction fails, use Tesseract OCR
        # 4. Clean and normalize text
        
        return "[PDF content placeholder]"
        
    async def _extract_html(self, document: Dict[str, Any]) -> str:
        """
        Extract clean text from HTML document
        
        Args:
            document: Document dictionary with HTML data
            
        Returns:
            Clean text
        """
        # TODO: Implement actual HTML fetching
        # For MVP, return placeholder
        logger.info(f"HTML extraction for {document.get('url')} (placeholder)")
        
        # In production:
        # 1. Fetch HTML from URL
        # 2. Use BeautifulSoup to parse
        # 3. Remove scripts, styles, navigation
        # 4. Extract main content
        # 5. Clean whitespace and normalize
        
        return "[HTML content placeholder]"
        
    async def _extract_xml(self, document: Dict[str, Any]) -> str:
        """
        Extract text from XML document
        
        Args:
            document: Document dictionary with XML data
            
        Returns:
            Extracted text
        """
        logger.info(f"XML extraction for {document.get('url')} (placeholder)")
        
        # In production:
        # 1. Fetch XML from URL
        # 2. Parse XML structure
        # 3. Extract relevant fields based on schema
        # 4. Convert to canonical JSON
        
        return "[XML content placeholder]"
        
    def _extract_metadata(self, document: Dict[str, Any], content: str) -> Dict[str, Any]:
        """
        Extract metadata from document and content
        
        Args:
            document: Raw document dictionary
            content: Extracted content
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            'title': document.get('title', ''),
            'url': document.get('url', ''),
            'source': document.get('source', ''),
            'category': document.get('category', ''),
            'document_type': document.get('document_type', ''),
            'language': document.get('language', 'en'),
        }
        
        # Try to extract additional metadata from content
        # Look for common patterns in legal documents
        
        # Extract date patterns
        date_pattern = r'\b(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\b'
        dates = re.findall(date_pattern, content)
        if dates:
            metadata['dates_mentioned'] = dates[:5]  # First 5 dates
            
        # Extract act/regulation numbers
        act_pattern = r'\b([A-Z]{1,2}\.?\s*\d{4},?\s*c\.?\s*\d+)\b'
        acts = re.findall(act_pattern, content)
        if acts:
            metadata['act_references'] = acts[:10]
            
        # Extract section numbers
        section_pattern = r'\bsection\s+(\d+)\b'
        sections = re.findall(section_pattern, content, re.IGNORECASE)
        if sections:
            metadata['sections'] = list(set(sections))[:20]
            
        # Jurisdiction extraction
        if 'jurisdiction' in document:
            metadata['jurisdiction'] = document['jurisdiction']
        else:
            # Try to infer from content
            if 'Canada' in content or 'Canadian' in content:
                metadata['jurisdiction'] = 'Canada'
                
        return metadata
        
    def _generate_hash(self, content: str) -> str:
        """
        Generate SHA-256 hash of content for deduplication
        
        Args:
            content: Document content
            
        Returns:
            Hash string
        """
        content_bytes = content.encode('utf-8')
        return hashlib.sha256(content_bytes).hexdigest()
        
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\-\(\)\[\]\'\"\/]', '', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove multiple consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
        
    async def create_diff(self, old_version: Dict[str, Any], new_version: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a diff between two versions of a document
        
        Args:
            old_version: Previous version of document
            new_version: New version of document
            
        Returns:
            Diff information
        """
        # Simple diff for MVP - just track if content changed
        diff = {
            'old_hash': old_version.get('content_hash'),
            'new_hash': new_version.get('content_hash'),
            'changed': old_version.get('content_hash') != new_version.get('content_hash'),
            'old_version': old_version.get('version', 1),
            'new_version': new_version.get('version', 1),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # TODO: Implement detailed diff using difflib or similar
        # For production, calculate actual line-by-line changes
        
        return diff
