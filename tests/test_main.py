"""
DocuSense - Root Endpoint Tests
"""


def test_root_endpoint(client):
    """Test the root endpoint returns API information."""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "name" in data
    assert "version" in data
    assert "docs" in data
    assert data["docs"] == "/docs"


def test_openapi_schema_available(client):
    """Test that OpenAPI schema is available."""
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
