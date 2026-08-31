import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
PUBLIC_HEADERS = {"X-API-Key": "veyra-public-client-token"}
ADMIN_HEADERS = {"X-API-Key": "veyra-admin-master-key"}

@pytest.fixture(autouse=True)
def clean_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()

def test_v4_system_identity_and_version():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert "4.0" in data["version"]
    assert data["service"] == "veyra-v4-platform"

def test_multi_provider_ncmrwf_routing():
    # Kolkata coordinate within NCMRWF / NEPS regional domain
    payload = {"location": "Kolkata", "latitude": 22.5726, "longitude": 88.3639, "lead_hours": 48}
    res = client.post("/v1/predict", json=payload, headers=PUBLIC_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["conformal_lower"] < data["conformal_upper"]
    assert data["provider_provenance"] in ["open-meteo-ensemble", "ncmrwf-neps-regional", "planetary-climatology-fallback"]

def test_conformal_interval_and_ood_novelty_presence():
    payload = {"location": "Tokyo", "latitude": 35.68, "longitude": 139.65, "lead_hours": 24}
    res = client.post("/v1/predict", json=payload, headers=PUBLIC_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "conformal_lower" in data and "conformal_upper" in data
    assert "novelty_score" in data
    assert isinstance(data["novelty_score"], float)
    assert data["trust_state"] in ["SUPPORTED", "DEGRADED"]

def test_location_resolver_endpoint():
    res = client.get("/v1/location/resolve?query=Meghalaya")
    assert res.status_code == 200
    data = res.json()
    assert round(data["latitude"], 2) == 25.58
    assert round(data["longitude"], 2) == 91.89