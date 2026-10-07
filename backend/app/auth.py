"""
RemitMind Authentication & Authorization Engine
Implements RFC 7519 JWT role-based access control (RBAC).
Supported roles: sender | analyst | admin | agent
Enforces secret resolution from environment with fallback dev mode token issuer.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import jwt
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel

from app.config import settings

# JWT Configuration sourced from environment
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

ALLOWED_ROLES = {"sender", "analyst", "admin", "agent"}

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    sub: str
    expires_in_seconds: int

class DevTokenRequest(BaseModel):
    role: str = "analyst"
    user_id: str = "u_analyst_01"
    name: Optional[str] = "Nusrat Jahan"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Encodes JWT payload with expiration and issue timestamp."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": "remitmind-auth-service"
    })
    secret = getattr(settings, "JWT_SECRET", "dev-remitmind-jwt-secret-key-32-bytes")
    return jwt.encode(to_encode, secret, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Decodes and validates signature and expiration of JWT."""
    secret = getattr(settings, "JWT_SECRET", "dev-remitmind-jwt-secret-key-32-bytes")
    try:
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "token_expired",
                "detail": "Authentication token has expired.",
                "detail_bn": "লগইন টোকেনের মেয়াদ শেষ হয়ে গেছে। দয়া করে পুনরায় প্রমাণীকরণ করুন।"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "token_invalid",
                "detail": "Provided authentication token is invalid or malformed.",
                "detail_bn": "প্রদত্ত টোকেনটি সঠিক নয় বা বিকৃত হয়েছে।"
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

def get_current_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> dict:
    """
    Resolves the caller identity and role.
    Supports standard Authorization: Bearer <token> and backward-compatible API keys.
    """
    # 1. Bearer Token Check
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return decode_access_token(parts[1])
        elif len(parts) == 1:
            # Tolerant parsing for raw token string in header
            return decode_access_token(parts[0])

    # 2. Configured Analyst API Key Check
    configured_key = getattr(settings, "ANALYST_API_KEY", "") or os.getenv("ANALYST_API_KEY", "")
    if x_api_key and configured_key and x_api_key == configured_key:
        return {
            "sub": "analyst_api_user",
            "role": "analyst",
            "name": "API Service Key",
            "auth_type": "api_key"
        }

    # 3. Dev-mode bypass token issuer header support (strictly disabled in production)
    dev_enabled = getattr(settings, "DEV_AUTH_ENABLED", True) and getattr(settings, "APP_ENV", "development") != "production"
    if dev_enabled and x_api_key and x_api_key.startswith("dev-"):
        role = x_api_key.replace("dev-", "")
        if role in ALLOWED_ROLES:
            return {
                "sub": f"dev_{role}_user",
                "role": role,
                "name": f"Dev {role.capitalize()}",
                "auth_type": "dev_key"
            }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": "unauthorized",
            "detail": "Authentication credentials were not provided or are invalid.",
            "detail_bn": "লগইন তথ্য প্রদান করা হয়নি অথবা প্রদত্ত তথ্য সঠিক নয়।"
        },
        headers={"WWW-Authenticate": "Bearer"}
    )

def get_optional_user(
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None)
) -> Optional[dict]:
    """Graceful caller identification without throwing 401 exceptions."""
    try:
        return get_current_user(authorization=authorization, x_api_key=x_api_key)
    except HTTPException:
        return None

def require_role(*allowed_roles: str):
    """
    FastAPI dependency factory enforcing specified role authorizations.
    Admin role possesses hierarchical superuser privileges.
    """
    def role_checker(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("role", "")
        if user_role not in allowed_roles and user_role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "forbidden",
                    "detail": f"Access denied. Required role in {list(allowed_roles)}, current role is '{user_role}'.",
                    "detail_bn": "অনুমোদন ব্যর্থ: এই কার্যক্রমে আপনার প্রয়োজনীয় অনুমতি নেই।",
                    "required_roles": list(allowed_roles),
                    "current_role": user_role
                }
            )
        return user
    return role_checker

from fastapi import APIRouter, Depends, HTTPException, Header, status, Request
from app.limiter import limiter

# ==============================================================================
# Dedicated Authentication & Dev-Token Issuer Router
# ==============================================================================
auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Access"])

@auth_router.post("/dev-token", response_model=TokenResponse)
@limiter.limit("5/minute")
def issue_dev_token(request: Request, req: DevTokenRequest):
    """
    Development-only JWT token issuer behind env flag.
    Allows frontend and automated tests to retrieve verified roles without manual sign-in.
    """
    dev_enabled = getattr(settings, "DEV_AUTH_ENABLED", True) and getattr(settings, "APP_ENV", "development") != "production"
    if not dev_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "dev_auth_disabled",
                "detail": "Dev token issuance is disabled in current environment.",
                "detail_bn": "উন্নয়ন মোড টোকেন বর্তমান পরিবেশে নিষ্ক্রিয় রয়েছে।"
            }
        )

    role = req.role.lower()
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role. Must be one of {list(ALLOWED_ROLES)}"
        )

    payload = {
        "sub": req.user_id,
        "role": role,
        "name": req.name
    }
    token = create_access_token(payload)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=role,
        sub=req.user_id,
        expires_in_seconds=ACCESS_TOKEN_EXPIRE_HOURS * 3600
    )

@auth_router.get("/dev-token", response_model=TokenResponse)
@limiter.limit("5/minute")
def get_dev_token_quick(request: Request, role: str = "analyst", user_id: str = "u_analyst_01"):
    """Quick GET endpoint for dev browser testing."""
    return issue_dev_token(request, DevTokenRequest(role=role, user_id=user_id))

@auth_router.get("/me")
def get_authenticated_profile(current_user: dict = Depends(get_current_user)):
    """Returns claims of the currently authenticated JWT or API key."""
    return {
        "status": "authenticated",
        "user": current_user
    }
