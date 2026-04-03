"""
ScholarClaw — Schemes Router
Scholarship scheme endpoints with eligibility matching.
"""

import json
import logging
from datetime import datetime
from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from db import prisma
from dependencies import get_current_user, CurrentUser

logger = logging.getLogger("schemes.router")

router = APIRouter(prefix="/api/schemes", tags=["Schemes"])


# ── Schemas ─────────────────────────────────────────────────────

class EligibilityCriteria(BaseModel):
    """Eligibility criteria for a scholarship scheme."""
    category: list[str] = Field(default_factory=list)
    income_limit: Optional[float] = None
    states: list[str] = Field(default_factory=list)
    education_levels: list[str] = Field(default_factory=list)
    min_percentage: Optional[float] = None
    max_age: Optional[int] = None
    gender: Optional[str] = None
    disability_required: bool = False


class SchemeResponse(BaseModel):
    """Single scholarship scheme response."""
    id: str
    name: str
    provider: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    deadline: Optional[datetime] = None
    eligibility_criteria: Optional[dict[str, Any]] = None
    required_documents: Optional[list[str]] = None
    application_url: Optional[str] = None
    is_active: bool = True
    match_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class SchemeListResponse(BaseModel):
    """Paginated list of schemes."""
    schemes: list[SchemeResponse]
    total: int
    page: int
    pages: int
    limit: int


class EligibilityCheckResponse(BaseModel):
    """Response for eligibility check."""
    scheme_id: str
    scheme_name: str
    is_eligible: bool
    match_score: float
    reasons: list[str]
    missing_criteria: list[str]


# ── Helper Functions ────────────────────────────────────────────

def parse_eligibility_criteria(criteria: any) -> dict:
    """Parse eligibility criteria from JSON string or dict."""
    if not criteria:
        return {}
    if isinstance(criteria, dict):
        return criteria
    if isinstance(criteria, str):
        try:
            return json.loads(criteria)
        except json.JSONDecodeError:
            return {}
    return {}


def parse_required_documents(docs: any) -> list:
    """Parse required documents from JSON string or list."""
    if not docs:
        return []
    if isinstance(docs, list):
        return docs
    if isinstance(docs, str):
        try:
            return json.loads(docs)
        except json.JSONDecodeError:
            return []
    return []


async def calculate_match_score(
    criteria: dict,
    profile: Optional[Any]
) -> tuple[float, list[str], list[str]]:
    """
    Calculate match score between a scheme's criteria and student profile.

    Returns:
        tuple: (match_score, matched_reasons, missing_criteria)
    """
    if not profile:
        return 0.0, [], ["No profile found - please complete your profile"]

    matched = []
    missing = []
    total_criteria = 0
    matched_criteria = 0

    # Category check
    if criteria.get("category"):
        total_criteria += 1
        profile_category = profile.category
        if profile_category and profile_category.upper() in [c.upper() for c in criteria["category"]]:
            matched_criteria += 1
            matched.append(f"Category matches: {profile_category}")
        elif not profile_category:
            missing.append("Category not specified in profile")
        else:
            missing.append(f"Category {profile_category} not in eligible: {criteria['category']}")

    # Income check
    if criteria.get("income_limit"):
        total_criteria += 1
        if profile.annualIncome is not None:
            if profile.annualIncome <= criteria["income_limit"]:
                matched_criteria += 1
                matched.append(f"Income ₹{profile.annualIncome:,.0f} within limit ₹{criteria['income_limit']:,.0f}")
            else:
                missing.append(f"Income ₹{profile.annualIncome:,.0f} exceeds limit ₹{criteria['income_limit']:,.0f}")
        else:
            missing.append("Annual income not specified in profile")

    # State check
    if criteria.get("states") and len(criteria["states"]) > 0:
        total_criteria += 1
        if profile.state:
            if profile.state in criteria["states"]:
                matched_criteria += 1
                matched.append(f"State {profile.state} is eligible")
            else:
                missing.append(f"State {profile.state} not in eligible states")
        else:
            missing.append("State not specified in profile")

    # Education level check
    if criteria.get("education_levels"):
        total_criteria += 1
        if profile.educationLevel:
            if profile.educationLevel in criteria["education_levels"]:
                matched_criteria += 1
                matched.append(f"Education level {profile.educationLevel} matches")
            else:
                missing.append(f"Education level {profile.educationLevel} not eligible")
        else:
            missing.append("Education level not specified in profile")

    # Percentage check
    if criteria.get("min_percentage"):
        total_criteria += 1
        if profile.percentage is not None:
            if profile.percentage >= criteria["min_percentage"]:
                matched_criteria += 1
                matched.append(f"Percentage {profile.percentage}% meets minimum {criteria['min_percentage']}%")
            else:
                missing.append(f"Percentage {profile.percentage}% below minimum {criteria['min_percentage']}%")
        else:
            missing.append("Percentage not specified in profile")

    # Gender check
    if criteria.get("gender"):
        total_criteria += 1
        if profile.gender:
            if profile.gender.upper() == criteria["gender"].upper():
                matched_criteria += 1
                matched.append(f"Gender {profile.gender} matches")
            else:
                missing.append(f"Gender {profile.gender} does not match required {criteria['gender']}")
        else:
            missing.append("Gender not specified in profile")

    # Disability check
    if criteria.get("disability_required"):
        total_criteria += 1
        if profile.disabilityStatus:
            matched_criteria += 1
            matched.append("Disability status verified")
        else:
            missing.append("Disability status required for this scheme")

    # Calculate score
    if total_criteria == 0:
        # No specific criteria - everyone is eligible
        return 100.0, ["Open to all students"], []

    score = (matched_criteria / total_criteria) * 100
    return round(score, 1), matched, missing


def scheme_to_response(scheme, match_score: Optional[float] = None) -> SchemeResponse:
    """Convert Prisma scheme to response model."""
    return SchemeResponse(
        id=scheme.id,
        name=scheme.name,
        provider=scheme.provider,
        description=scheme.description,
        amount=scheme.amount,
        deadline=scheme.deadline,
        eligibility_criteria=parse_eligibility_criteria(scheme.eligibilityCriteria),
        required_documents=parse_required_documents(scheme.requiredDocuments),
        application_url=scheme.applicationUrl,
        is_active=getattr(scheme, 'isActive', True),  # Default to True if not present
        match_score=match_score,
        created_at=scheme.createdAt,
        updated_at=scheme.updatedAt,
    )


# ── List Schemes ────────────────────────────────────────────────

@router.get("", response_model=SchemeListResponse)
async def list_schemes(
    current_user: CurrentUser = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None, description="Filter by category"),
    state: Optional[str] = Query(None, description="Filter by state"),
    active_only: bool = Query(True, description="Only show active schemes"),
):
    """
    List all scholarship schemes with optional filtering.

    Returns schemes with match scores based on user's profile.
    """
    try:
        logger.info(f"list_schemes called by user {current_user.id}")

        # Get total count
        total = await prisma.scholarshipscheme.count()
        logger.info(f"Total schemes in database: {total}")

        # Calculate pagination
        skip = (page - 1) * limit
        pages = (total + limit - 1) // limit if total > 0 else 1

        # Get schemes
        schemes = await prisma.scholarshipscheme.find_many(
            order={"createdAt": "desc"},
            skip=skip,
            take=limit,
        )
        logger.info(f"Fetched {len(schemes)} schemes")

        # Get user's profile for match scoring
        profile = await prisma.studentprofile.find_unique(
            where={"userId": current_user.id}
        )
        logger.info(f"User profile found: {profile is not None}")

        # Process schemes with match scores
        scheme_responses = []
        for scheme in schemes:
            try:
                criteria = parse_eligibility_criteria(scheme.eligibilityCriteria)

                # Apply category filter if specified
                if category:
                    scheme_categories = criteria.get("category", [])
                    if scheme_categories and category.upper() not in [c.upper() for c in scheme_categories]:
                        continue

                # Apply state filter if specified
                if state:
                    scheme_states = criteria.get("states", [])
                    if scheme_states and state not in scheme_states:
                        continue

                # Calculate match score
                match_score, _, _ = await calculate_match_score(criteria, profile)

                scheme_responses.append(scheme_to_response(scheme, match_score))
            except Exception as e:
                logger.error(f"Error processing scheme {scheme.id}: {e}")
                continue

        # Sort by match score (highest first)
        scheme_responses.sort(key=lambda s: s.match_score or 0, reverse=True)

        return SchemeListResponse(
            schemes=scheme_responses,
            total=len(scheme_responses),
            page=page,
            pages=pages,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Error in list_schemes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Get Single Scheme ───────────────────────────────────────────

@router.get("/{scheme_id}", response_model=SchemeResponse)
async def get_scheme(
    scheme_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get a single scholarship scheme by ID.
    """
    scheme = await prisma.scholarshipscheme.find_unique(
        where={"id": scheme_id}
    )

    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme {scheme_id} not found",
        )

    # Get profile and calculate match score
    profile = await prisma.studentprofile.find_unique(
        where={"userId": current_user.id}
    )

    criteria = parse_eligibility_criteria(scheme.eligibilityCriteria)
    match_score, _, _ = await calculate_match_score(criteria, profile)

    return scheme_to_response(scheme, match_score)


# ── Check Eligibility ───────────────────────────────────────────

@router.post("/{scheme_id}/check-eligibility", response_model=EligibilityCheckResponse)
async def check_eligibility(
    scheme_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Check if the current user is eligible for a specific scheme.

    Returns detailed eligibility information including match score,
    matched criteria, and missing requirements.
    """
    scheme = await prisma.scholarshipscheme.find_unique(
        where={"id": scheme_id}
    )

    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme {scheme_id} not found",
        )

    # Get user's profile
    profile = await prisma.studentprofile.find_unique(
        where={"userId": current_user.id}
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete your profile first to check eligibility",
        )

    criteria = parse_eligibility_criteria(scheme.eligibilityCriteria)
    match_score, matched_reasons, missing_criteria = await calculate_match_score(
        criteria, profile
    )

    return EligibilityCheckResponse(
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        is_eligible=match_score >= 50.0,  # Consider eligible if 50%+ match
        match_score=match_score,
        reasons=matched_reasons,
        missing_criteria=missing_criteria,
    )


# ── Draft Application ───────────────────────────────────────────

@router.post("/{scheme_id}/draft-application")
async def draft_application(
    scheme_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate a draft application for a scheme.

    This endpoint can be extended to integrate with AI agents
    for intelligent application drafting.
    """
    scheme = await prisma.scholarshipscheme.find_unique(
        where={"id": scheme_id}
    )

    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scheme {scheme_id} not found",
        )

    # Get user's profile
    profile = await prisma.studentprofile.find_unique(
        where={"userId": current_user.id}
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please complete your profile first",
        )

    # Return draft info (can be extended with AI integration)
    return {
        "scheme_id": scheme.id,
        "scheme_name": scheme.name,
        "application_url": scheme.applicationUrl,
        "required_documents": parse_required_documents(scheme.requiredDocuments),
        "deadline": scheme.deadline.isoformat() if scheme.deadline else None,
        "message": "Please gather the required documents and apply through the official portal.",
    }
