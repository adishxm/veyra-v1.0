import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "veyra-public-client-token"}

GOLDEN_LOCATIONS = [
    # Polar & Extreme Cold
    {"name": "South Pole Plateau", "lat": -82.5, "lon": 0.0, "lead": 48, "min_temp": -70.0, "max_temp": -35.0},
    {"name": "Tromso Arctic", "lat": 69.65, "lon": 18.95, "lead": 48, "min_temp": 2.0, "max_temp": 18.0},
    {"name": "Svalbard", "lat": 78.22, "lon": 15.65, "lead": 48, "min_temp": 0.0, "max_temp": 15.0},
    # Subtropical Deserts & Hot Summer
    {"name": "Riyadh Desert", "lat": 23.7, "lon": 45.0, "lead": 48, "min_temp": 24.0, "max_temp": 46.0},
    {"name": "Phoenix", "lat": 33.45, "lon": -112.07, "lead": 48, "min_temp": 20.0, "max_temp": 44.0},
    {"name": "Cairo", "lat": 30.04, "lon": 31.24, "lead": 48, "min_temp": 20.0, "max_temp": 38.0},
    # Tropical & Maritime
    {"name": "Kolkata", "lat": 22.57, "lon": 88.36, "lead": 48, "min_temp": 22.0, "max_temp": 36.0},
    {"name": "Singapore", "lat": 1.35, "lon": 103.82, "lead": 48, "min_temp": 24.0, "max_temp": 34.0},
    {"name": "Miami", "lat": 25.76, "lon": -80.19, "lead": 48, "min_temp": 24.0, "max_temp": 35.0},
    # Mid-Latitude Temperate & High Altitude
    {"name": "London", "lat": 51.51, "lon": -0.13, "lead": 48, "min_temp": 10.0, "max_temp": 26.0},
    {"name": "Tokyo", "lat": 35.68, "lon": 139.65, "lead": 48, "min_temp": 12.0, "max_temp": 32.0},
    {"name": "Denver High Altitude", "lat": 39.74, "lon": -104.99, "lead": 48, "min_temp": 8.0, "max_temp": 30.0},
    {"name": "Sydney (Southern Winter)", "lat": -33.87, "lon": 151.21, "lead": 48, "min_temp": 8.0, "max_temp": 22.0}
]

@pytest.mark.parametrize("loc", GOLDEN_LOCATIONS)
def test_climate_band_physical_plausibility(loc):
    """Asserts that conformal intervals fall strictly within physical climatological envelopes."""
    payload = {
        "location": loc["name"],
        "latitude": loc["lat"],
        "longitude": loc["lon"],
        "lead_hours": loc["lead"],
        "variable": "temperature_2m"
    }
    response = client.post("/v1/predict", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()

    c_low = data["conformal_lower"]
    c_high = data["conformal_upper"]
    center = (c_low + c_high) / 2.0

    # 1. Interval Ordering Check
    assert c_low < c_high, f"Inverted interval for {loc['name']}: [{c_low}, {c_high}]"

    # 2. Dynamic Spread Margin Check
    margin = (c_high - c_low) / 2.0
    assert 2.5 <= margin <= 8.5, f"Uncalibrated conformal margin ({margin}°C) for {loc['name']}"

    # 3. Climatological Plausibility Check
    assert loc["min_temp"] <= center <= loc["max_temp"], (
        f"{loc['name']} center ({center}°C) violates physical boundary "
        f"[{loc['min_temp']}°C, {loc['max_temp']}°C]"
    )

def test_hot_climate_no_clamping():
    """Verifies that Tokyo, Miami, and Phoenix receive distinct regional forecasts."""
    targets = [
        {"name": "Tokyo", "lat": 35.68, "lon": 139.65},
        {"name": "Miami", "lat": 25.76, "lon": -80.19},
        {"name": "Phoenix", "lat": 33.45, "lon": -112.07}
    ]
    results = []
    for t in targets:
        res = client.post(
            "/v1/predict",
            json={"location": t["name"], "latitude": t["lat"], "longitude": t["lon"], "lead_hours": 48},
            headers=AUTH_HEADERS
        )
        assert res.status_code == 200
        results.append(res.json()["conformal_lower"])

    # Assert no two cities in different climates share identical clamped boundaries
    assert len(set(results)) == len(results), f"Clamping detected across distinct cities: {results}"