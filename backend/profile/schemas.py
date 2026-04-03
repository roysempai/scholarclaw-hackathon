"""
ScholarClaw — Profile Schemas
Pydantic models for student profile endpoints.
"""

from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class Category(str, Enum):
    """Student category for reservation."""
    GENERAL = "GEN"
    OBC = "OBC"
    SC = "SC"
    ST = "ST"


class Gender(str, Enum):
    """Gender options."""
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


# ── Request Schemas ─────────────────────────────────────────────

class ProfileCreateRequest(BaseModel):
    """Create student profile request."""
    gender: Optional[str] = None
    category: Optional[str] = Field(None, description="GEN, OBC, SC, ST")
    annual_income: Optional[float] = Field(None, alias="annualIncome", ge=0)
    state: Optional[str] = Field(None, max_length=50)
    district: Optional[str] = Field(None, max_length=100)
    education_level: Optional[str] = Field(None, alias="educationLevel", max_length=50)
    institution: Optional[str] = Field(None, max_length=200)
    course: Optional[str] = Field(None, max_length=100)
    percentage: Optional[float] = Field(None, ge=0, le=100)
    disability_status: Optional[bool] = Field(False, alias="disabilityStatus")

    class Config:
        populate_by_name = True


class ProfileUpdateRequest(BaseModel):
    """Update student profile request."""
    full_name: Optional[str] = None  # Accepted but stored in User table
    date_of_birth: Optional[str] = None  # Accepted for future use
    gender: Optional[str] = None
    category: Optional[str] = None
    annual_income: Optional[float] = Field(None, alias="annualIncome", ge=0)
    state: Optional[str] = None
    district: Optional[str] = None
    education_level: Optional[str] = Field(None, alias="educationLevel")
    institution: Optional[str] = None
    course: Optional[str] = None
    percentage: Optional[float] = Field(None, ge=0, le=100)
    disability_status: Optional[bool] = Field(None, alias="disabilityStatus")

    class Config:
        populate_by_name = True
        extra = "ignore"  # Ignore extra fields like full_name, date_of_birth


# ── Response Schemas ────────────────────────────────────────────

class ProfileResponse(BaseModel):
    """Student profile response."""
    id: str
    user_id: str
    full_name: Optional[str] = None  # From User table
    gender: Optional[str] = None
    category: Optional[str] = None
    annual_income: Optional[float] = None
    state: Optional[str] = None
    district: Optional[str] = None
    education_level: Optional[str] = None
    institution: Optional[str] = None
    course: Optional[str] = None
    percentage: Optional[float] = None
    disability_status: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
