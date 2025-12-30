import pytest
from agents.sources_canada import get_all_sources, get_priority_sources, flatten_all_urls

def test_get_all_sources():
    """Test that all sources are returned correctly"""
    sources = get_all_sources()
    
    assert "federal" in sources
    assert "quebec" in sources
    assert "ontario" in sources
    assert "pdfs" in sources
    
    # Check federal has nested structure
    assert isinstance(sources["federal"], dict)
    assert "prestations" in sources["federal"]
    
def test_get_priority_sources():
    """Test priority sources list"""
    priority = get_priority_sources()
    
    assert isinstance(priority, list)
    assert len(priority) == 6
    # Check all are valid URLs
    for url in priority:
        assert url.startswith(("http://", "https://"))

def test_flatten_all_urls():
    """Test URL flattening utility"""
    sources = get_all_sources()
    all_urls = flatten_all_urls(sources)
    
    assert isinstance(all_urls, list)
    assert len(all_urls) == 27
    # Check all are strings and valid URLs
    for url in all_urls:
        assert isinstance(url, str)
        assert url.startswith(("http://", "https://"))
    
def test_flatten_all_urls_with_simple_dict():
    """Test flattening with simple structure"""
    simple_sources = {
        "category1": ["url1", "url2"],
        "category2": ["url3"]
    }
    result = flatten_all_urls(simple_sources)
    assert result == ["url1", "url2", "url3"]

def test_flatten_all_urls_with_nested_dict():
    """Test flattening with nested structure"""
    nested_sources = {
        "category1": {
            "sub1": ["url1", "url2"],
            "sub2": ["url3"]
        },
        "category2": ["url4"]
    }
    result = flatten_all_urls(nested_sources)
    assert len(result) == 4
    assert "url1" in result
    assert "url4" in result
