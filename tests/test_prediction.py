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
    assert body["trust_state"] == "SUPPORTED"
    assert body["abstain"] is False
    assert 0 <= body["bust_probability"] <= 1
    assert body["model_version"] == "personal-veyra-transparent-baseline-v1"
    assert body["feature_schema_version"] == "personal-veyra-features-v1"


def test_prediction_requires_coordinates_for_v01() -> None:
    response = client.post("/v1/predict", json={"location": "Kolkata"})
    assert response.status_code == 422
    assert "latitude and longitude" in response.json()["detail"]
