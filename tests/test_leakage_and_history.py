import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from backend.app.services.weather_adapters import (
    OpenMeteoAdapter,
    NCMRWFNEPSAdapter,
    PlanetaryPhysicsFallback,
    MultiProviderWeatherOrchestrator
)
from backend.app.ml.conformal_ood_engine import ConformalOODSentinel

# 1. Anti-Data-Leakage Verification
def test_zero_future_leakage_in_forecast_extraction():
    """Asserts that all extracted features strictly originate from issue-time data."""
    now_utc = datetime.now(timezone.utc)
    lead_hours = 48
    
    adapter = OpenMeteoAdapter()
    data = asyncio.run(adapter.fetch_forecast(22.5726, 88.3639, lead_hours=lead_hours))
    
    issue_dt = datetime.fromisoformat(data["issue_time"])
    valid_dt = datetime.fromisoformat(data["valid_time"])
    
    # Assert issue time is not in the future
    assert issue_dt <= now_utc + timedelta(minutes=5)
    # Assert valid time strictly equals issue time + lead horizon
    assert abs((valid_dt - issue_dt).total_seconds() - (lead_hours * 3600)) < 120
    # Assert strictly issue-time features are present (no ground truth error labels)
    assert "error" not in data and "actual_value" not in data
    assert "ensemble_spread" in data and data["ensemble_spread"] >= 0.0

# 2. Conformal Coverage & Marginal Validity
def test_split_conformal_coverage_bounds():
    """Verifies that split-conformal bounds adapt monotonically with ensemble dispersion."""
    low_dispersion_feat = {"temperature": 25.0, "ensemble_spread": 0.8, "temp_variance": 0.2, "lead_hours": 24}
    high_dispersion_feat = {"temperature": 25.0, "ensemble_spread": 3.5, "temp_variance": 1.8, "lead_hours": 24}
    
    _, _, low_c_low, low_c_high, _, _ = ConformalOODSentinel.evaluate(low_dispersion_feat, 0.10)
    _, _, high_c_low, high_c_high, _, _ = ConformalOODSentinel.evaluate(high_dispersion_feat, 0.10)
    
    low_margin = (low_c_high - low_c_low) / 2.0
    high_margin = (high_c_high - high_c_low) / 2.0
    
    # Higher dispersion must yield a wider conformal uncertainty margin
    assert high_margin > low_margin
    assert 2.8 <= low_margin <= 8.5
    assert 2.8 <= high_margin <= 8.5

# 3. Regional NCMRWF / NEPS Domain Isolation
def test_ncmrwf_domain_rejection_outside_south_asia():
    """Asserts that NCMRWF adapter rejects requests outside its South Asian bounding box."""
    adapter = NCMRWFNEPSAdapter()
    # London coordinates (outside South Asia domain)
    with pytest.raises(ValueError, match="Coordinates outside NCMRWF regional domain"):
        asyncio.run(adapter.fetch_forecast(51.5074, -0.1278, lead_hours=24))
