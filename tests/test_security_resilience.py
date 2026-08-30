import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
PUBLIC_HEADERS = {"X-API-Key": "veyra-public-client-token"}
ADMIN_HEADERS = {"X-API-Key": "veyra-admin-master-key"}

@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    """Ensure no stale mock dependencies leak into security verification."""
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()

# 1. RBAC and Endpoint Gating
def test_admin_retrain_requires_admin_privilege():
    res = client.post("/v1/admin/retrain", headers=PUBLIC_HEADERS)
    assert res.status_code == 403

def test_public_cannot_read_internal_logs():
    res = client.get("/v1/logs", headers=PUBLIC_HEADERS)
    assert res.status_code in [403, 404]

def test_unauthenticated_request_rejected():
    res = client.post("/v1/predict", json={"location": "Kolkata", "latitude": 22.57, "longitude": 88.36})
    assert res.status_code == 401

# 2. Input Boundary and Non-Finite Rejections
@pytest.mark.parametrize("bad_lat", [90.0001, -90.0001, "invalid", None])
def test_invalid_latitude_boundary(bad_lat):
    payload = {"location": "Test", "latitude": bad_lat, "longitude": 88.36, "lead_hours": 48}
    res = client.post("/v1/predict", json=payload, headers=PUBLIC_HEADERS)
    assert res.status_code == 422

@pytest.mark.parametrize("bad_lead", [0, 241, -24, 1e10, "lead"])
def test_invalid_lead_hours_boundary(bad_lead):
    payload = {"location": "Test", "latitude": 22.57, "longitude": 88.36, "lead_hours": bad_lead}
    res = client.post("/v1/predict", json=payload, headers=PUBLIC_HEADERS)
    assert res.status_code == 422

# 3. Synchronous Batch Overload Protection
def test_batch_sync_cap_enforced():
    items = [{"location": "Kolkata", "latitude": 22.57, "longitude": 88.36, "lead_hours": 24} for _ in range(55)]
    res = client.post("/v1/predict/batch", json={"items": items}, headers=PUBLIC_HEADERS)
    assert res.status_code == 400

# 4. Single-Item Failure Isolation in Batch Processing
def test_batch_failure_isolation():
    payload = {
        "items": [
            {"location": "Kolkata", "latitude": 22.57, "longitude": 88.36, "lead_hours": 24},
            {"location": "Atlantis", "latitude": -999.0, "longitude": -999.0, "lead_hours": 24},
            {"location": "London", "latitude": 51.51, "longitude": -0.13, "lead_hours": 48}
        ]
    }
    res = client.post("/v1/predict/batch", json=payload, headers=PUBLIC_HEADERS)
    assert res.status_code == 200
    results = res.json().get("results", [])
    assert len(results) == 3
    assert results[0]["abstain"] is False or results[0].get("success") is True
    assert results[1]["abstain"] is True or results[1].get("error") is not None or results[1].get("success") is False
    assert results[2]["abstain"] is False or results[2].get("success") is True
