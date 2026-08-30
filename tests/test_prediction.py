from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_prediction_returns_structured_supported_result() -> None:
    response = client.post(
        "/v1/predict",
        json={
            "location": "Kolkata",
            "latitude": 22.5726,
            "longitude": 88.3639,
            "variable": "temperature_2m",
            "lead_hours": 48,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["trust_state"] in ("SUPPORTED", "DEGRADED")
    assert body["abstain"] is False
    assert 0.0 <= body["bust_probability"] <= 1.0
    assert body["model_version"] == "personal-veyra-transparent-baseline-v2"
    assert body["feature_schema_version"] == "personal-veyra-features-v2"
    assert isinstance(body["evidence"], list)


def test_prediction_requires_lat_lon() -> None:
    response = client.post(
        "/v1/predict",
        json={
            "location": "Kolkata",
            "variable": "temperature_2m",
            "lead_hours": 48,
        },
    )
    assert response.status_code == 422


def test_prediction_logs_endpoint() -> None:
    # Query logs endpoint after prediction has run
    response = client.get("/v1/logs?limit=5")
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) >= 1
    assert "location" in logs[0]
    assert "bust_probability" in logs[0]