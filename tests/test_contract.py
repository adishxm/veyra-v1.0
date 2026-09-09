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
    first = data["timeseries"][0]
    assert "provider_1" in first and "provider_2" in first
    assert "date_label" in first and "year_label" in first
    assert 0.05 <= first["provider_1"] <= 0.35
    assert 0.05 <= first["provider_2"] <= 0.35
