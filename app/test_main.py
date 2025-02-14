import uuid
from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def get_auth_headers():
    """Helper to get authenticated headers."""
    response = client.post("/api/v1/login/token",
        data={
            "username": "admin",
            "password": "admin",
            "scope": "superuser",
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_authentication():
    """Test authentication endpoints."""
    # Unauthenticated requests
    response = client.get("/api/v1/user")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    
    # Password authentication
    response = client.post("/api/v1/login/token",
        data={
            "username": "admin",
            "password": "admin",
            "scope": "superuser",
        }
    )
    assert response.status_code == 200
    assert len(response.json()["access_token"]) > 0

def test_user_endpoints():
    """Test user management endpoints."""
    headers = get_auth_headers()

    # Get current user
    response = client.get("/api/v1/user", headers=headers)
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["id"] == "admin"
    assert user_data["status"] == "active"

    # Update current user
    update_data = {
        "name": "Admin User",
        "email": "admin@example.com",
        "data": {"preferences": {"theme": "dark"}}
    }
    response = client.patch("/api/v1/user", 
        headers=headers,
        json=update_data
    )
    assert response.status_code == 200
    updated_user = response.json()
    assert updated_user["name"] == update_data["name"]
    assert updated_user["email"] == update_data["email"]
    assert updated_user["data"] == update_data["data"]

def test_resource_endpoints():
    """Test resource management endpoints."""
    headers = get_auth_headers()

    # Create resource
    new_resource = {
        "name": "Test Resource",
        "data": {"type": "test", "value": 123}
    }
    response = client.post("/api/v1/resources",
        headers=headers,
        json=new_resource
    )
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == new_resource["name"]
    assert created["data"] == new_resource["data"]
    resource_id = created["id"]

    # Get all resources
    response = client.get("/api/v1/resources",
        headers=headers,
        params={"skip": 0, "size": 100}
    )
    assert response.status_code == 200
    resources = response.json()
    assert len(resources) > 0
    assert any(r["id"] == resource_id for r in resources)

    # Get single resource
    response = client.get(f"/api/v1/resources/{resource_id}",
        headers=headers
    )
    assert response.status_code == 200
    resource = response.json()
    assert resource["id"] == resource_id
    assert resource["name"] == new_resource["name"]

    # Update resource
    update_data = {
        "name": "Updated Resource",
        "data": {"type": "test", "value": 456}
    }
    response = client.patch(f"/api/v1/resources/{resource_id}",
        headers=headers,
        json=update_data
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == update_data["name"]
    assert updated["data"] == update_data["data"]

    # Replace resource
    replace_data = {
        "name": "Replaced Resource",
        "data": {"type": "test", "value": 789}
    }
    response = client.put(f"/api/v1/resources/{resource_id}",
        headers=headers,
        json=replace_data
    )
    print(response.json())
    assert response.status_code == 200
    replaced = response.json()
    assert replaced["name"] == replace_data["name"]
    assert replaced["data"] == replace_data["data"]

    # Delete resource
    response = client.delete(f"/api/v1/resources/{resource_id}",
        headers=headers
    )
    assert response.status_code == 204

    # Verify deletion
    response = client.get(f"/api/v1/resources/{resource_id}",
        headers=headers
    )
    assert response.status_code == 404

def test_error_cases():
    """Test error handling for various scenarios."""
    headers = get_auth_headers()

    # Invalid resource ID
    response = client.get("/api/v1/resources/invalid-uuid",
        headers=headers
    )
    assert response.status_code == 422

    # Non-existent resource
    random_uuid = str(uuid.uuid4())
    response = client.get(f"/api/v1/resources/{random_uuid}",
        headers=headers
    )
    assert response.status_code == 404

    # Invalid resource data
    response = client.post("/api/v1/resources",
        headers=headers,
        json={"invalid": "data"}
    )
    assert response.status_code == 422

    # Invalid query parameters
    response = client.get("/api/v1/resources",
        headers=headers,
        params={"size": -1}
    )
    assert response.status_code == 422
