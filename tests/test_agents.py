import pytest
import io
from main import agent_extract_pdf_text

def test_pdf_extraction_basic():
    """Test extraction de texte PDF basique"""
    # PDF minimal valide
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj
xref
0 4
trailer<</Size 4/Root 1 0 R>>
%%EOF"""
    
    result = agent_extract_pdf_text(pdf_content)
    assert isinstance(result, str)

def test_pdf_extraction_empty():
    """Test extraction PDF vide ne crash pas"""
    result = agent_extract_pdf_text(b"")
    assert result == ""
