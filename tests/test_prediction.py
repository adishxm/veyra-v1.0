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


def test_prediction_logs_and_verification_cycle() -> None:
    # 1. Fetch latest prediction log
    logs_res = client.get("/v1/logs?limit=1")
    assert logs_res.status_code == 200
    logs = logs_res.json()
    assert len(logs) >= 1
    pred_id = logs[0]["id"]

    # 2. Log actual observation
    actual_res = client.post(
        "/v1/actuals",
        json={
            "prediction_id": pred_id,
            "actual_value": 31.5,
            "bust_error_threshold": 2.5,
        },
    )
    assert actual_res.status_code == 200
    assert actual_res.json()["status"] == "verified"

    # 3. Check metrics computation
    metrics_res = client.get("/v1/metrics")
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["verified_count"] >= 1
    assert "brier_score" in metrics