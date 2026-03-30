"""
DocuSense - Items Endpoint Tests
"""
import pytest

from app.api.v1.endpoints.items import items_db, item_counter


@pytest.fixture(autouse=True)
def reset_items_db():
    """Reset the items database before each test."""
    global item_counter
    items_db.clear()
    # Reset counter by importing and modifying the module-level variable
    import app.api.v1.endpoints.items as items_module
    items_module.item_counter = 0
    yield
    items_db.clear()
    items_module.item_counter = 0


class TestCreateItem:
    """Tests for creating items."""

    def test_create_item_success(self, client, sample_item):
        """Test creating a new item successfully."""
        response = client.post("/api/v1/items/", json=sample_item)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["id"] == 1
        assert data["name"] == sample_item["name"]
        assert data["description"] == sample_item["description"]
        assert data["price"] == sample_item["price"]
        assert data["is_active"] == sample_item["is_active"]

    def test_create_item_minimal(self, client):
        """Test creating an item with minimal required fields."""
        item = {"name": "Minimal Item", "price": 10.00}
        response = client.post("/api/v1/items/", json=item)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == "Minimal Item"
        assert data["price"] == 10.00
        assert data["description"] is None
        assert data["is_active"] is True  # Default value

    def test_create_item_invalid_price(self, client):
        """Test creating an item with invalid price fails."""
        item = {"name": "Invalid Item", "price": -10.00}
        response = client.post("/api/v1/items/", json=item)
        
        assert response.status_code == 422  # Validation error

    def test_create_item_missing_name(self, client):
        """Test creating an item without name fails."""
        item = {"price": 10.00}
        response = client.post("/api/v1/items/", json=item)
        
        assert response.status_code == 422  # Validation error


class TestGetItem:
    """Tests for getting items."""

    def test_get_item_success(self, client, sample_item):
        """Test getting an existing item."""
        # First create an item
        create_response = client.post("/api/v1/items/", json=sample_item)
        item_id = create_response.json()["id"]
        
        # Then get it
        response = client.get(f"/api/v1/items/{item_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == item_id
        assert data["name"] == sample_item["name"]

    def test_get_item_not_found(self, client):
        """Test getting a non-existent item returns 404."""
        response = client.get("/api/v1/items/999")
        
        assert response.status_code == 404
        assert response.json()["detail"] == "Item not found"


class TestListItems:
    """Tests for listing items."""

    def test_list_items_empty(self, client):
        """Test listing items when database is empty."""
        response = client.get("/api/v1/items/")
        
        assert response.status_code == 200
        assert response.json() == []

    def test_list_items_with_data(self, client, sample_item):
        """Test listing items with data."""
        # Create multiple items
        client.post("/api/v1/items/", json=sample_item)
        client.post("/api/v1/items/", json={**sample_item, "name": "Item 2"})
        
        response = client.get("/api/v1/items/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2

    def test_list_items_pagination(self, client, sample_item):
        """Test listing items with pagination."""
        # Create 5 items
        for i in range(5):
            client.post("/api/v1/items/", json={**sample_item, "name": f"Item {i}"})
        
        # Test skip
        response = client.get("/api/v1/items/?skip=2&limit=2")
        data = response.json()
        
        assert len(data) == 2
        assert data[0]["name"] == "Item 2"


class TestUpdateItem:
    """Tests for updating items."""

    def test_update_item_success(self, client, sample_item, sample_item_update):
        """Test updating an existing item."""
        # Create an item
        create_response = client.post("/api/v1/items/", json=sample_item)
        item_id = create_response.json()["id"]
        
        # Update it
        response = client.put(f"/api/v1/items/{item_id}", json=sample_item_update)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == sample_item_update["name"]
        assert data["price"] == sample_item_update["price"]
        # Original description should remain
        assert data["description"] == sample_item["description"]

    def test_update_item_not_found(self, client, sample_item_update):
        """Test updating a non-existent item returns 404."""
        response = client.put("/api/v1/items/999", json=sample_item_update)
        
        assert response.status_code == 404


class TestDeleteItem:
    """Tests for deleting items."""

    def test_delete_item_success(self, client, sample_item):
        """Test deleting an existing item."""
        # Create an item
        create_response = client.post("/api/v1/items/", json=sample_item)
        item_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/api/v1/items/{item_id}")
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/items/{item_id}")
        assert get_response.status_code == 404

    def test_delete_item_not_found(self, client):
        """Test deleting a non-existent item returns 404."""
        response = client.delete("/api/v1/items/999")
        
        assert response.status_code == 404
