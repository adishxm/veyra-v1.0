import time
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status, Header

VALID_CLIENT_TOKENS = {"veyra-public-client-token", "veyra-demo-token", "veyra-client-v1"}
VALID_ADMIN_TOKENS = {"veyra-admin-master-key", "veyra-root-admin", "veyra-adm-prod-2026"}

RATE_LIMIT_STORE: Dict[str, list] = {}
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 60

def check_rate_limit(request: Request, user: dict) -> None:
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()

    if client_ip not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[client_ip] = []

    RATE_LIMIT_STORE[client_ip] = [t for t in RATE_LIMIT_STORE[client_ip] if now - t < RATE_LIMIT_WINDOW]

    if len(RATE_LIMIT_STORE[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Maximum 60 requests per minute.",
            headers={"Retry-After": "60"}
        )

    RATE_LIMIT_STORE[client_ip].append(now)

async def require_auth_user(request: Request, x_api_key: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    api_key = x_api_key or request.headers.get("x-api-key") or request.headers.get("X-API-Key")

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing X-API-Key header"
        )

    if api_key in VALID_ADMIN_TOKENS:
        return {"user_id": "admin-master", "role": "admin", "token": api_key}

    if api_key in VALID_CLIENT_TOKENS:
        return {"user_id": "public-client", "role": "user", "token": api_key}

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Invalid API key"
    )

async def require_admin_user(request: Request, x_api_key: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    user = await require_auth_user(request, x_api_key)
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin master privilege required"
        )
    return user

async def optional_auth_user(request: Request, x_api_key: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    api_key = x_api_key or request.headers.get("x-api-key") or request.headers.get("X-API-Key")
    if not api_key:
        return {"user_id": "anonymous", "role": "guest", "token": None}
    try:
        return await require_auth_user(request, x_api_key)
    except HTTPException:
        return {"user_id": "anonymous", "role": "guest", "token": None}
