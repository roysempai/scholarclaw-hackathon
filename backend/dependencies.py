"""
ScholarClaw — FastAPI Dependencies
Common dependencies for dependency injection.
"""

from typing import Annotated
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from config import settings
from db import prisma


# ── Security Scheme ──────────────────────────────────────────────
security = HTTPBearer()


# ── User Model ───────────────────────────────────────────────────
@dataclass
class CurrentUser:
    """Represents the authenticated user from JWT."""
    id: str
    email: str
    role: str
    fullName: str = ""


# ── Rate Limiting State ──────────────────────────────────────────
# In-memory daily rate limit tracking (per user)
# In production, use Redis for distributed rate limiting
_user_request_counts: dict[str, dict] = {}
DAILY_RATE_LIMIT = 100  # requests per user per day


def check_user_rate_limit(user_id: str) -> bool:
    """
    Check if user has exceeded daily rate limit.

    Returns True if within limit, raises HTTPException if exceeded.
    """
    today = datetime.now(timezone.utc).date().isoformat()

    if user_id not in _user_request_counts:
        _user_request_counts[user_id] = {"date": today, "count": 0}

    user_data = _user_request_counts[user_id]

    # Reset counter if it's a new day
    if user_data["date"] != today:
        _user_request_counts[user_id] = {"date": today, "count": 0}
        user_data = _user_request_counts[user_id]

    if user_data["count"] >= DAILY_RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily rate limit exceeded. Maximum {DAILY_RATE_LIMIT} requests per day.",
        )

    user_data["count"] += 1
    return True


# ── JWT Token Validation ─────────────────────────────────────────
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> CurrentUser:
    """
    Validate JWT token and return current user.

    Raises HTTPException 401 if token is invalid or expired.
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id: str = payload.get("sub")
        email: str = payload.get("email", "")
        role: str = payload.get("role", "user")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Optionally verify user still exists in database
        user = await prisma.user.find_unique(where={"id": user_id})
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.isActive:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return CurrentUser(
            id=user.id,
            email=user.email,
            role=user.role,
            fullName=user.fullName,
        )

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Dependency Types ─────────────────────────────────────────────
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
