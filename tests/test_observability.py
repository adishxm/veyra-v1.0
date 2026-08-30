from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_prometheus_metrics_endpoint() -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    text = response.text
    assert "veyra_predictions_total" in text
    assert "veyra_abstentions_total" in text
    assert "veyra_risk_tier_total" in text