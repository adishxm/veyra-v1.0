import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_batch_prediction_endpoint() -> None:
    payload = {
        "items": [
            {
                "location": "Kolkata",
                "latitude": 22.5726,
                "longitude": 88.3639,
                "variable": "temperature_2m",
                "lead_hours": 24,
            },
            {
                "location": "Delhi",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "variable": "temperature_2m",
                "lead_hours": 48,
            },
            {
                "location": "InvalidLocation",
                "variable": "temperature_2m",
                "lead_hours": 24,
            },
        ]
    }
    response = client.post("/v1/predict/batch", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_requested"] == 3
    assert data["successful_count"] == 2
    assert data["failed_count"] == 1
    assert data["results"][0]["success"] is True
    assert data["results"][2]["success"] is False


def test_async_jobs_lifecycle() -> None:
    payload = {
        "items": [
            {
                "location": "Mumbai",
                "latitude": 19.0760,
                "longitude": 72.8777,
                "variable": "temperature_2m",
                "lead_hours": 24,
            }
        ]
    }
    # 1. Enqueue job
    create_res = client.post("/v1/jobs/predict", json=payload)
    assert create_res.status_code == 200
    job_data = create_res.json()
    job_id = job_data["job_id"]
    assert job_data["status"] == "PENDING"

    # 2. Poll status
    time.sleep(1.0)
    poll_res = client.get(f"/v1/jobs/{job_id}")
    assert poll_res.status_code == 200
    status_data = poll_res.json()
    assert status_data["status"] in ("PROCESSING", "COMPLETED")


from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "veyra-public-client-token"}

def test_batch_prediction_endpoint() -> None:
    payload = {
        "items": [
            {"location": "Kolkata", "latitude": 22.5726, "longitude": 88.3639, "variable": "temperature_2m", "lead_hours": 24},
            {"location": "Delhi", "latitude": 28.6139, "longitude": 77.2090, "variable": "temperature_2m", "lead_hours": 48},
            {"location": "InvalidLocation", "variable": "temperature_2m", "lead_hours": 24}
        ]
    }
    response = client.post("/v1/predict/batch", json=payload, headers=AUTH_HEADERS)
    assert response.status_code == 200

def test_async_jobs_lifecycle() -> None:
    payload = {
        "items": [
            {"location": "Mumbai", "latitude": 19.0760, "longitude": 72.8777, "variable": "temperature_2m", "lead_hours": 24}
        ]
    }
    create_res = client.post("/v1/jobs/predict", json=payload, headers=AUTH_HEADERS)
    assert create_res.status_code == 200
    job_id = create_res.json()["job_id"]
    get_res = client.get(f"/v1/jobs/{job_id}", headers=AUTH_HEADERS)
    assert get_res.status_code == 200