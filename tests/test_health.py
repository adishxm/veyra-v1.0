from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "veyra-v4-platform"
    assert "4.0" in data["version"]
