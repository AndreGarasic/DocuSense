"""
DocuSense - Health Endpoint Tests
"""


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/v1/health/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "message" in data


def test_readiness_check(client):
    """Test the readiness check endpoint."""
    response = client.get("/api/v1/health/ready")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ready"
    assert "message" in data
