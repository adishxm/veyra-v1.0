import time
from typing import Optional, Dict
from collections import defaultdict
from fastapi import Header, HTTPException, Request, status

VALID_KEYS = {
    "veyra-live-key-prod-001": {"user_id": "prod-admin", "role": "admin", "rate_limit": 120},
    "veyra-public-client-token": {"user_id": "public-web-user", "role": "client", "rate_limit": 60},
}

# Sliding window rate limiter: identifier -> list of timestamps
RATE_LIMIT_BUCKETS = defaultdict(list)

def check_rate_limit(request: Request, user: dict):
    """Enforces per-key sliding window rate limit with Retry-After headers."""
    identifier = user.get("user_id") or (request.client.host if request.client else "anonymous")
    limit = user.get("rate_limit", 60)
    now = time.time()
    
    # Prune timestamps older than 60 seconds
    timestamps = [t for t in RATE_LIMIT_BUCKETS[identifier] if now - t < 60.0]
    
    if len(timestamps) >= limit:
        retry_after = int(60.0 - (now - timestamps[0])) if timestamps else 60
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: maximum {limit} requests per minute.",
            headers={"Retry-After": str(max(1, retry_after))}
        )
        
    timestamps.append(now)
    RATE_LIMIT_BUCKETS[identifier] = timestamps

def require_auth_user(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> dict:
    """Strictly validates presence of X-API-Key. Rejects missing or bad credentials with 401."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required X-API-Key header"
        )
    if x_api_key not in VALID_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return VALID_KEYS[x_api_key]

def optional_auth_user(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> Optional[dict]:
    """Optional auth for public health/status probes."""
    if not x_api_key:
        return None
    if x_api_key not in VALID_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return VALID_KEYS[x_api_key]