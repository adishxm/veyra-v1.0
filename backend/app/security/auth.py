import time
from collections import defaultdict
from fastapi import HTTPException, Security, Request, status
from fastapi.security.api_key import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Pre-configured demo API keys (Admin and Standard Tenant)
VALID_API_KEYS = {
    "veyra-live-key-prod-001": {"user_id": "tenant_enterprise", "role": "admin", "rate_limit": 120},
    "veyra-public-demo-token": {"user_id": "public_viewer", "role": "viewer", "rate_limit": 60}
}

# In-memory sliding window rate limiter
RATE_LIMIT_STORE = defaultdict(list)

async def get_current_user(api_key: str = Security(api_key_header)):
    if not api_key:
        # Allow open public viewer access if no header supplied
        return {"user_id": "anonymous_viewer", "role": "viewer", "rate_limit": 30}
    
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API Key credential"
        )
    return VALID_API_KEYS[api_key]

def check_rate_limit(request: Request, user: dict):
    client_ip = request.client.host if request.client else "127.0.0.1"
    key = f"{user['user_id']}:{client_ip}"
    now = time.time()
    
    # Prune timestamps older than 60 seconds
    RATE_LIMIT_STORE[key] = [ts for ts in RATE_LIMIT_STORE[key] if now - ts < 60]
    
    if len(RATE_LIMIT_STORE[key]) >= user["rate_limit"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {user['rate_limit']} requests per minute"
        )
    RATE_LIMIT_STORE[key].append(now)