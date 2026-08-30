import pytest
from backend.app.main import app
from backend.app.security.auth import require_auth_user, require_admin_user, optional_auth_user

@pytest.fixture(autouse=True)
def override_auth_for_tests():
    admin_ctx = {
        "user_id": "test_runner",
        "role": "admin",
        "rate_limit": 1000
    }
    app.dependency_overrides[require_auth_user] = lambda: admin_ctx
    app.dependency_overrides[require_admin_user] = lambda: admin_ctx
    app.dependency_overrides[optional_auth_user] = lambda: admin_ctx
    yield
    app.dependency_overrides.clear()