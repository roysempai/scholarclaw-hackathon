"""
ScholarClaw — Authentication Router
User registration, login, logout, and token refresh.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import secrets

from config import settings
from db import prisma
from auth.schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
)
from auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from dependencies import get_current_user, CurrentUser

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


# ── Rate Limiting (in-memory for demo) ─────────────────────────
_ip_request_counts: dict[str, dict] = {}


def check_rate_limit(request: Request, limit: int, window_minutes: int = 1):
    """Simple IP-based rate limiting."""
    ip = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)
    key = f"{ip}:{window_minutes}"

    if key not in _ip_request_counts:
        _ip_request_counts[key] = {"count": 0, "reset": now + timedelta(minutes=window_minutes)}

    data = _ip_request_counts[key]
    if now > data["reset"]:
        data["count"] = 0
        data["reset"] = now + timedelta(minutes=window_minutes)

    if data["count"] >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {window_minutes} minute(s).",
        )
    data["count"] += 1


# ── Register ────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: Request, body: RegisterRequest):
    """
    Register a new user.

    Rate limit: 3 requests per minute per IP.
    """
    check_rate_limit(request, limit=3, window_minutes=1)

    # Check if email already exists
    existing_user = await prisma.user.find_unique(where={"email": body.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    hashed_pw = hash_password(body.password)
    user = await prisma.user.create(
        data={
            "email": body.email,
            "password": hashed_pw,
            "fullName": body.full_name,
            "role": body.role.value,
        }
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.fullName,
        role=user.role,
        created_at=user.createdAt,
    )


# ── Login ───────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest):
    """
    Authenticate user and return JWT tokens.

    Rate limit: 5 requests per minute per IP.
    Security: Always returns "Invalid credentials" — never reveals if email exists.
    """
    check_rate_limit(request, limit=5, window_minutes=1)

    # Find user
    user = await prisma.user.find_unique(where={"email": body.email})

    # Always take the same time regardless of whether user exists (timing attack prevention)
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.isActive:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        )

    # Create tokens
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id, user.role)

    # Store refresh token in database
    await prisma.refreshtoken.create(
        data={
            "userId": user.id,
            "token": refresh_token,
            "expiresAt": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        }
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ── Refresh Token ───────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    """
    Exchange a valid refresh token for a new access token.

    Only returns a new access token; refresh token remains the same.
    """
    try:
        payload = decode_token(body.refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")

        # Verify token exists in database
        stored_token = await prisma.refreshtoken.find_first(
            where={
                "token": body.refresh_token,
                "userId": user_id,
            }
        )

        if not stored_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        if stored_token.expiresAt < datetime.now(timezone.utc):
            # Delete expired token
            await prisma.refreshtoken.delete(where={"id": stored_token.id})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
            )

        # Get user for role
        user = await prisma.user.find_unique(where={"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        # Create new access token
        access_token = create_access_token(user.id, user.role)

        return TokenResponse(
            access_token=access_token,
            refresh_token=body.refresh_token,  # Keep same refresh token
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


# ── Get Current User ────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_current_user_endpoint(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current authenticated user's profile.

    Requires valid JWT access token in Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.fullName,
        role=current_user.role,
        created_at=datetime.now(timezone.utc),  # Would need to fetch from DB for actual created_at
    )


# ── Logout ──────────────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: Optional[RefreshRequest] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Logout user by invalidating their refresh token.

    If refresh_token is provided, deletes that specific token.
    Otherwise, deletes all refresh tokens for the user.
    """
    if body and body.refresh_token:
        # Delete specific token
        await prisma.refreshtoken.delete_many(
            where={
                "userId": current_user.id,
                "token": body.refresh_token,
            }
        )
    else:
        # Delete all tokens for user
        await prisma.refreshtoken.delete_many(
            where={"userId": current_user.id}
        )

    return MessageResponse(message="Logged out successfully")
