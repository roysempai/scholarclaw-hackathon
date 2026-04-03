"""
ScholarClaw — Profile Router
Student profile CRUD endpoints.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from db import prisma
from dependencies import get_current_user, CurrentUser
from profile.schemas import (
    ProfileCreateRequest,
    ProfileUpdateRequest,
    ProfileResponse,
)

router = APIRouter(prefix="/api/profile", tags=["Profile"])


# ── Helper Function ─────────────────────────────────────────────

def profile_to_response(profile, full_name: str = None) -> ProfileResponse:
    """Convert Prisma profile to response schema."""
    return ProfileResponse(
        id=profile.id,
        user_id=profile.userId,
        full_name=full_name,
        gender=profile.gender,
        category=profile.category,
        annual_income=profile.annualIncome,
        state=profile.state,
        district=profile.district,
        education_level=profile.educationLevel,
        institution=profile.institution,
        course=profile.course,
        percentage=profile.percentage,
        disability_status=profile.disabilityStatus,
        created_at=profile.createdAt,
        updated_at=profile.updatedAt,
    )


# ── Create Profile ──────────────────────────────────────────────

@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    body: ProfileCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create student profile for authenticated user.

    Only one profile per user is allowed.
    """
    # Check if profile already exists
    existing = await prisma.studentprofile.find_unique(
        where={"userId": current_user.id}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists. Use PUT to update.",
        )

    # Create profile
    profile = await prisma.studentprofile.create(
        data={
            "userId": current_user.id,
            "gender": body.gender if body.gender else None,
            "category": body.category,
            "annualIncome": body.annual_income,
            "state": body.state,
            "district": body.district,
            "educationLevel": body.education_level,
            "institution": body.institution,
            "course": body.course,
            "percentage": body.percentage,
            "disabilityStatus": body.disability_status,
        }
    )

    return profile_to_response(profile, current_user.fullName)


# ── Get Profile ─────────────────────────────────────────────────

@router.get("", response_model=ProfileResponse)
async def get_profile(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get authenticated user's profile.
    """
    profile = await prisma.studentprofile.find_unique(
        where={"userId": current_user.id}
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Create one first.",
        )

    return profile_to_response(profile, current_user.fullName)


# ── Update Profile ──────────────────────────────────────────────

@router.put("", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Update authenticated user's profile.
    Creates a new profile if one doesn't exist (upsert behavior).
    """
    # Check if profile exists
    existing = await prisma.studentprofile.find_unique(
        where={"userId": current_user.id}
    )

    # Build data from body
    profile_data = {}
    if body.gender is not None:
        # Handle both enum and string values
        gender_value = body.gender.value if hasattr(body.gender, 'value') else body.gender
        profile_data["gender"] = gender_value
    if body.category is not None:
        profile_data["category"] = body.category
    if body.annual_income is not None:
        profile_data["annualIncome"] = body.annual_income
    if body.state is not None:
        profile_data["state"] = body.state
    if body.district is not None:
        profile_data["district"] = body.district
    if body.education_level is not None:
        profile_data["educationLevel"] = body.education_level
    if body.institution is not None:
        profile_data["institution"] = body.institution
    if body.course is not None:
        profile_data["course"] = body.course
    if body.percentage is not None:
        profile_data["percentage"] = body.percentage
    if body.disability_status is not None:
        profile_data["disabilityStatus"] = body.disability_status

    if not existing:
        # Create new profile if doesn't exist (upsert behavior)
        profile_data["userId"] = current_user.id
        profile = await prisma.studentprofile.create(data=profile_data)
    elif not profile_data:
        return profile_to_response(existing, current_user.fullName)
    else:
        # Update existing profile
        profile = await prisma.studentprofile.update(
            where={"userId": current_user.id},
            data=profile_data,
        )

    return profile_to_response(profile, current_user.fullName)


# ── Delete Profile ──────────────────────────────────────────────

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(current_user: CurrentUser = Depends(get_current_user)):
    """
    Delete authenticated user's profile.
    """
    # Check if profile exists
    existing = await prisma.studentprofile.find_unique(
        where={"userId": current_user.id}
    )

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )

    # Delete profile
    await prisma.studentprofile.delete(
        where={"userId": current_user.id}
    )

    return None
