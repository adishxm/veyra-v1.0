import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
AUTH_KEY = {"X-API-Key": "veyra-public-client-token"}
KOLKATA = {
    "location": "Kolkata",
    "latitude": 22.56,
    "longitude": 88.36,
    "variable": "temperature_2m",
    "lead_hours": 24
}

def post(body, headers=AUTH_KEY):
    return client.post("/v1/predict", json=body, headers=headers)

def test_health_ok():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_determinism():
    a = post(KOLKATA).json()
    b = post(KOLKATA).json()
    assert a["bust_probability"] == b["bust_probability"]

def test_monotone_in_lead():
    ps = [post({**KOLKATA, "lead_hours": lead}).json()["bust_probability"] for lead in (24, 72, 120, 240)]
    assert ps == sorted(ps)

def test_interval_brackets_point():
    d = post(KOLKATA).json()
    assert d["p_bust_interval"]["lower"] <= d["bust_probability"] <= d["p_bust_interval"]["upper"]

def test_abstain_returns_nulls():
    d = post({**KOLKATA, "latitude": -89.9, "longitude": 0.0, "lead_hours": 240}).json()
    assert d["abstain"] is True
    assert d["bust_probability"] is None
    assert d["p_bust_interval"] is None
    assert "OOD_ABSTAIN" in d["reason_codes"]

def test_cross_endpoint_agreement():
    p = post(KOLKATA).json()["bust_probability"]
    batch_res = client.post("/v1/predict/batch", json={"items": [KOLKATA]}, headers=AUTH_KEY).json()
    assert batch_res["results"][0]["bust_probability"] == p

@pytest.mark.parametrize("lead", [0, -5, 999])
def test_invalid_lead_rejected(lead):
    assert post({**KOLKATA, "lead_hours": lead}).status_code == 422

def test_coords_out_of_bounds():
    assert post({**KOLKATA, "latitude": 91.0}).status_code == 422

def test_auth_required():
    assert client.post("/v1/predict", json=KOLKATA).status_code == 401

def test_scoring_mode_declared():
    res = post(KOLKATA).json()
    assert res["scoring_mode"] in {"ANALYTIC_REGIME_PRIOR", "ML_ARTIFACT_PLATT_GBM"}

def test_unknown_replay_case_rejected():
    res = post({"location": "Kolkata", "replay_case": "phantom_case_999"})
    assert res.status_code == 404
    assert res.json()["detail"]["code"] == "REPLAY_CASE_NOT_FOUND"

def test_location_xss_sanitized():
    res = post({"location": "<script>alert('xss')</script>", "latitude": 22.56, "longitude": 88.36})
    assert res.status_code == 200
    assert "<script>" not in res.json()["location"]
    assert "&lt;script&gt;" in res.json()["location"]

def test_polar_analogs_and_explanations_suppressed():
    res_exp = client.get("/v1/explanation?latitude=-89.9&longitude=0.0&lead_hours=48&variable=temperature_2m", headers=AUTH_KEY)
    assert res_exp.status_code == 200
    assert res_exp.json()["feature_attributions"] == []

    res_ana = client.get("/v1/analogs?latitude=-89.9&longitude=0.0&lead_hours=48&variable=temperature_2m", headers=AUTH_KEY)
    assert res_ana.status_code == 200
    assert res_ana.json()["analogs"] == []

def test_checksums_match():
    import hashlib
    with open("CHECKSUMS.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            expected_hash, file_path = line.split("  ")
            with open(file_path, "rb") as target:
                actual_hash = hashlib.sha256(target.read()).hexdigest()
            assert actual_hash.lower() == expected_hash.lower()

def test_historical_bust_timeseries_contract():
    res = client.get("/v1/historical-bust-timeseries?latitude=28.6139&longitude=77.2090")
    assert res.status_code == 200
    data = res.json()
    assert "timeseries" in data
    assert len(data["timeseries"]) >= 100
    assert data["provider_1_name"] == "NCMRWF / IMD (NEPS)"
    assert data["provider_2_name"] == "ECMWF IFS (Global ENS)"
    assert data["horizon_days"] == 90
    first = data["timeseries"][0]
    assert "provider_1" in first and "provider_2" in first
    assert "date_label" in first and "year_label" in first
    assert 0.05 <= first["provider_1"] <= 0.35
    assert 0.05 <= first["provider_2"] <= 0.35

    res_us = client.get("/v1/historical-bust-timeseries?latitude=40.71&longitude=-74.00")
    assert res_us.status_code == 200
    assert res_us.json()["provider_1_name"] == "NOAA NWS (GEFS v12)"

def test_risk_trajectory_is_public():
    res = client.get("/v1/risk-trajectory?latitude=22.56&longitude=88.36&variable=temperature_2m")
    assert res.status_code == 200
    data = res.json()
    assert "trajectory" in data
    assert len(data["trajectory"]) == 5

def test_replay_scoring_mode_honest_fixture():
    res = post({"replay_case": "bengaluru_case"}).json()
    assert res["scoring_mode"] == "FROZEN_REPLAY_FIXTURE"

def test_polar_abstain_scoring_mode_safety():
    res = post({**KOLKATA, "latitude": -89.9, "longitude": 0.0, "lead_hours": 240}).json()
    assert res["scoring_mode"] == "SAFETY_ABSTENTION"

def test_openapi_security_operations_declared():
    schema = app.openapi()
    for path, item in schema.get("paths", {}).items():
        for method, op in item.items():
            if method in ["get", "post", "put", "delete", "patch"] and isinstance(op, dict):
                assert "security" in op and op["security"] == [{"ApiKeyAuth": []}]

def test_all_schema_routes_typed():
    from fastapi.routing import APIRoute
    for r in app.routes:
        if isinstance(r, APIRoute) and r.include_in_schema:
            assert r.response_model is not None, f"Untyped route found: {r.path}"

def test_metrics_truth_and_reconciliation():
    res = client.get("/v1/metrics")
    assert res.status_code == 200
    m = res.json()
    assert m["status"] == "MEASURED"
    assert m["pr_auc"] == 0.1709
    assert m["spread_only_pr_auc"] == 0.1258
    assert m["gain_over_spread_only_pct"] == 35.83
    assert m["brier_score"] == 0.0409
    assert m["offline_test_sample_count"] == 892
    assert m["train_calibration_test_split"] == [2676, 892, 892]
    assert m["artifact_sha256"] == "08bbbc9a7fbca0c1c005ece5b0fc42245e700f774e37d48b16351eab3d285494"

def test_security_headers_present():
    res = client.get("/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("Referrer-Policy") == "no-referrer"
    assert "max-age" in res.headers.get("Strict-Transport-Security", "")

def test_risk_multiple_and_unclamped_resolution():
    res = post({**KOLKATA, "lead_hours": 24})
    assert res.status_code == 200
    data = res.json()
    assert "risk_multiple" in data
    assert data["risk_multiple"] == round(data["bust_probability"] / 0.05, 2)
    # Ensure artificial 0.08 clamp is removed (can be below 0.08 if raw model output is small)
    assert 0.01 <= data["bust_probability"] <= 0.95

def test_openapi_all_routes_have_error_schemas():
    schema = app.openapi()
    paths = schema.get("paths", {})
    assert len(paths) >= 20
    assert "ErrorEnvelope" in schema.get("components", {}).get("schemas", {})
    for path, path_item in paths.items():
        for method in ["get", "post", "put", "delete", "patch"]:
            if method in path_item:
                responses = path_item[method].get("responses", {})
                assert "401" in responses, f"Route {method.upper()} {path} missing 401 schema"
                assert "429" in responses, f"Route {method.upper()} {path} missing 429 schema"

def test_metrics_detail_full_suite():
    res = client.get("/v1/metrics?detail=full")
    assert res.status_code == 200
    m = res.json()
    # §10.3 Calibration Slope & Intercept
    assert "calibration_slope" in m
    assert 0.8 <= m["calibration_slope"] <= 1.25
    assert "calibration_intercept" in m
    # Log loss
    assert "log_loss" in m
    assert 0.05 <= m["log_loss"] <= 0.50
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

