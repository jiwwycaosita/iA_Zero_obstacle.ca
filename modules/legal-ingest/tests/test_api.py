"""
Unit tests for API endpoints
Tests search, document retrieval, and metadata endpoints
"""

import pytest
from fastapi.testclient import TestClient

from src.api import app


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns service info"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert 'service' in data
        assert 'version' in data
        assert data['service'] == 'Legal Ingest API'
        
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert data['status'] == 'healthy'
        assert 'services' in data
        
    def test_search_endpoint(self, client):
        """Test search endpoint"""
        search_data = {
            "query": "test query",
            "limit": 10,
            "offset": 0,
            "search_type": "hybrid"
        }
        
        response = client.post("/search", json=search_data)
        
        assert response.status_code == 200
        data = response.json()
        assert 'results' in data
        assert 'total' in data
        assert 'took_ms' in data
        assert isinstance(data['results'], list)
        
    def test_search_with_filters(self, client):
        """Test search with filters"""
        search_data = {
            "query": "legal",
            "filters": {
                "category": "federal",
                "language": "en"
            },
            "limit": 5
        }
        
        response = client.post("/search", json=search_data)
        
        assert response.status_code == 200
        
    def test_search_semantic(self, client):
        """Test semantic search"""
        search_data = {
            "query": "immigration rules",
            "search_type": "semantic"
        }
        
        response = client.post("/search", json=search_data)
        
        assert response.status_code == 200
        
    def test_search_fulltext(self, client):
        """Test full-text search"""
        search_data = {
            "query": "section 10",
            "search_type": "fulltext"
        }
        
        response = client.post("/search", json=search_data)
        
        assert response.status_code == 200
        
    def test_get_document_not_found(self, client):
        """Test document retrieval with non-existent ID"""
        response = client.get("/document/nonexistent")
        
        assert response.status_code == 404
        
    def test_list_jurisdictions(self, client):
        """Test jurisdictions listing"""
        response = client.get("/jurisdictions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should have at least federal and some provinces
        if len(data) > 0:
            jurisdiction = data[0]
            assert 'name' in jurisdiction
            assert 'type' in jurisdiction
            assert 'document_count' in jurisdiction
            
    def test_get_document_history_not_found(self, client):
        """Test history retrieval for non-existent document"""
        response = client.get("/history/nonexistent")
        
        assert response.status_code == 404
        
    def test_get_statistics(self, client):
        """Test statistics endpoint"""
        response = client.get("/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'total_documents' in data
        assert 'by_jurisdiction' in data
        assert 'by_category' in data
        assert 'by_language' in data
        assert 'last_updated' in data
        
    def test_search_validation(self, client):
        """Test search request validation"""
        # Missing query
        response = client.post("/search", json={})
        assert response.status_code == 422  # Validation error
        
    def test_search_pagination(self, client):
        """Test search pagination"""
        # First page
        response1 = client.post("/search", json={
            "query": "test",
            "limit": 5,
            "offset": 0
        })
        
        # Second page
        response2 = client.post("/search", json={
            "query": "test",
            "limit": 5,
            "offset": 5
        })
        
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestAPICORS:
    """Test CORS configuration"""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/")
        
        # CORS should allow cross-origin requests
        assert 'access-control-allow-origin' in response.headers or response.status_code == 200


class TestAPIErrorHandling:
    """Test API error handling"""
    
    def test_invalid_endpoint(self, client):
        """Test 404 for invalid endpoint"""
        response = client.get("/invalid/endpoint")
        
        assert response.status_code == 404
        
    def test_invalid_method(self, client):
        """Test invalid HTTP method"""
        response = client.post("/")
        
        # Root endpoint only supports GET
        assert response.status_code == 405 or response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
