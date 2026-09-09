from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "veyra-public-client-token"}
ADMIN_HEADERS = {"X-API-Key": "veyra-admin-master-key"}


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
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["trust_state"] in ("SUPPORTED", "DEGRADED")
    assert body["abstain"] is False
    assert 0.0 <= body["bust_probability"] <= 1.0
    assert "conformal_lower" in body
    assert "conformal_upper" in body
    assert body["conformal_lower"] < body["conformal_upper"]
    assert "novelty_score" in body
    assert "veyra-v2-champion-histgbm" in body["model_version"]
    assert "risk_multiple" in body


def test_prediction_requires_lat_lon() -> None:
    response = client.post(
        "/v1/predict",
        json={
            "location": "Kolkata",
            "variable": "temperature_2m",
            "lead_hours": 48,
        },
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 422


def test_model_registry_endpoint() -> None:
    response = client.get("/v1/models", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["active_champion"] == "veyra-v2-champion-histgbm"
    assert len(data["models"]) >= 2
    champion = next(m for m in data["models"] if m["model_id"] == "veyra-v2-champion-histgbm")
    assert champion["evaluation_status"] == "MEASURED"
    assert champion["metrics"]["pr_auc"] == 0.1709


def test_prediction_logs_and_verification_cycle() -> None:
    # Trigger a prediction first so logs has an entry
    pred_res = client.post(
        "/v1/predict",
        json={
            "location": "Kolkata",
            "latitude": 22.5726,
            "longitude": 88.3639,
            "variable": "temperature_2m",
            "lead_hours": 48,
        },
        headers=AUTH_HEADERS,
    )
    assert pred_res.status_code == 200

    logs_res = client.get("/v1/logs?limit=1", headers=ADMIN_HEADERS)
    assert logs_res.status_code == 200
    logs_data = logs_res.json()
    assert len(logs_data["logs"]) >= 1
    pred_id = logs_data["logs"][0]["request_id"]

    actual_res = client.post(
        "/v1/actuals",
        json={
            "location": "Kolkata",
            "latitude": 22.5726,
            "longitude": 88.3639,
            "variable": "temperature_2m",
            "lead_hours": 48,
            "observed_temperature": 31.5,
            "predicted_temperature": 29.0,
            "observed_value": 31.5,
            "predicted_value": 29.0,
            "bust_error_threshold": 2.5,
        },
        headers=ADMIN_HEADERS,
    )
    assert actual_res.status_code == 200
    assert actual_res.json()["status"] == "ingested"

    metrics_res = client.get("/v1/metrics", headers=AUTH_HEADERS)
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["verified_count"] >= 1
    assert "brier_score" in metrics