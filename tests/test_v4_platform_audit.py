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

def test_metrics_and_coverage_risk_curve():
    res = client.get("/v1/metrics")
    assert res.status_code == 200
    m = res.json()
    # §11.4 Coverage-risk curve
    assert "coverage_risk_curve" in m
    crc = m["coverage_risk_curve"]
    assert len(crc) >= 5
    assert "retained_brier" in crc[0]
    assert "abstention_rate" in crc[0]
    assert "high_conf_error_rate" in crc[0]
    # §9.16 Audit fix: fabricated bootstrap CI removed, honest note present
    assert "bootstrap_ci_note" in m
    assert "block_bootstrap_ci" not in m

def test_retrain_endpoint_honest_not_implemented():
    """Audit §9.20: Retrain endpoint must return NOT_IMPLEMENTED, not fake success."""
    res = client.post("/v1/admin/retrain", headers=ADMIN_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "NOT_IMPLEMENTED"

def test_prediction_transparency_fields():
    """Audit §9: predictions must include method disclosures."""
    payload = {"location": "Kolkata", "latitude": 22.56, "longitude": 88.36, "lead_hours": 24}
    res = client.post("/v1/predict", json=payload, headers=PUBLIC_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["conformal_method"] == "ANALYTIC_SPREAD_MARGIN"
    assert data["stability_method"] == "HEURISTIC_FORMULA"
    assert data["ambiguity_method"] == "DECISION_BOUNDARY_PROXIMITY"
    assert "variable_support_status" in data
    assert data["bust_definition"].startswith("q95 of |forecast - ERA5| on synthetic")

def test_model_registry_monotonic_ladder():
    """Audit §9.14: Champion E4 must have highest PR-AUC in registry."""
    res = client.get("/v1/models")
    assert res.status_code == 200
    models = res.json()["models"]
    champion = [m for m in models if m["stage"] == "active"][0]
    baselines = [m for m in models if m["stage"] == "baseline"]
    for b in baselines:
        assert champion["metrics"]["pr_auc"] > b["metrics"]["pr_auc"], (
            f"Champion PR-AUC {champion['metrics']['pr_auc']} not > baseline {b['model_id']} PR-AUC {b['metrics']['pr_auc']}"
        )

def test_reliability_diagram_bins_sum_to_test_set():
    """Audit §9.17: Reliability diagram bin counts must sum to offline_test_sample_count."""
    res = client.get("/v1/metrics")
    assert res.status_code == 200
    m = res.json()
    total_samples = sum(b["sample_count"] for b in m["reliability_diagram"])
    assert total_samples == m["offline_test_sample_count"]

def test_location_resolver_endpoint():
    res = client.get("/v1/location/resolve?query=Meghalaya")
    assert res.status_code == 200
    data = res.json()
    assert round(data["latitude"], 2) == 25.58
    assert round(data["longitude"], 2) == 91.89
    assert data["resolved"] is True

def test_location_resolver_unknown_returns_unresolved():
    """Audit §9.21: Unknown locations must return resolved=False, not fabricated coords."""
    res = client.get("/v1/location/resolve?query=RandomUnknownVillage12345")
    assert res.status_code == 200
    data = res.json()
    assert data["resolved"] is False
    assert data["latitude"] is None
    assert data["longitude"] is None