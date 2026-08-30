import pytest
from backend.app.main import app
from backend.app.security.auth import require_auth_user, optional_auth_user

@pytest.fixture(autouse=True)
def override_auth_for_tests():
    app.dependency_overrides[require_auth_user] = lambda: {
        "user_id": "test_suite_runner",
        "role": "admin",
        "rate_limit": 1000
    }
    app.dependency_overrides[optional_auth_user] = lambda: {
        "user_id": "test_suite_runner",
        "role": "admin",
        "rate_limit": 1000
    }
    yield
    app.dependency_overrides.clear()