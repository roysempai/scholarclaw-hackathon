"""
ScholarClaw — Authentication Schemas
Pydantic models for auth endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class Role(str, Enum):
    """User roles — simplified to 2 roles only."""
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


# ── Request Schemas ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=1, max_length=100)
    role: Role = Field(default=Role.STUDENT, description="User role (default: STUDENT)")


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


# ── Response Schemas ────────────────────────────────────────────

class UserResponse(BaseModel):
    """User data response (excludes sensitive fields)."""
    id: str
    email: str
    full_name: str
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    """JWT token pair response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
