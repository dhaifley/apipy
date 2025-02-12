from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_main():
    response = client.get("/api/v1/user")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}
    
    response = client.post(url="/api/v1/login/token",
        data={
            "username": "admin",
            "password": "admin",
            "scope":" superuser",
        }
    )
    assert response.status_code == 200
    print (response.json())
    assert len(response.json()["access_token"]) > 0
    client.headers = {
        "Authorization": "Bearer " + response.json()["access_token"],
    }

    response = client.get("/api/v1/user")
    assert response.status_code == 200
    assert response.json()["id"] == "admin"
