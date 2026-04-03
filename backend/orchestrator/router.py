"""
ScholarClaw — Orchestrator Router
API endpoints for the LangGraph orchestrator.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from dependencies import get_current_user, check_user_rate_limit, CurrentUser
from orchestrator.graph import run_orchestrator
from exceptions import PolicyBlockedError, AgentError

router = APIRouter(prefix="/api/orchestrator", tags=["Orchestrator"])


# ── Request/Response Schemas ─────────────────────────────────────


class OrchestratorRequest(BaseModel):
    """Request body for orchestrator run."""
    action: str = Field(
        ...,
        description="Action to perform: 'check_eligibility', 'generate_draft', or 'set_reminder'"
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional data for the action (scheme_id, profile overrides, etc.)"
    )


class OrchestratorResponse(BaseModel):
    """Response from orchestrator run."""
    success: bool
    action: str
    blocked: bool = False
    block_reason: Optional[str] = None
    eligibility_result: Optional[dict[str, Any]] = None
    draft: Optional[str] = None
    error: Optional[str] = None


# ── Orchestrator Endpoint ────────────────────────────────────────


@router.post("/run", response_model=OrchestratorResponse)
async def run_orchestrator_endpoint(
    request: Request,
    body: OrchestratorRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Run the LangGraph orchestrator.

    Requires JWT authentication. Enforces per-user daily rate limit.

    Actions:
    - `check_eligibility`: Check student eligibility for a scheme
    - `generate_draft`: Generate application draft for a scheme
    - `set_reminder`: Set a deadline reminder (handled by reminder agent)

    Request body:
    - `action`: The action to perform
    - `data`: Additional data (e.g., `scheme_id`, profile overrides)

    Returns:
    - `success`: Whether the operation completed successfully
    - `blocked`: Whether the request was blocked by policy
    - `eligibility_result`: Result if action was check_eligibility
    - `draft`: Generated draft if action was generate_draft
    """
    # Enforce rate limit
    check_user_rate_limit(current_user.id)

    try:
        # Get student profile from database
        from db import prisma

        profile = await prisma.studentprofile.find_unique(
            where={"userId": current_user.id}
        )

        student_profile = {}
        if profile:
            student_profile = {
                "name": current_user.fullName,
                "category": profile.category,
                "income": profile.annualIncome,
                "annualIncome": profile.annualIncome,
                "state": profile.state,
                "course": profile.course,
                "year": profile.educationLevel,
                "marks_12th": profile.percentage,
                "percentage": profile.percentage,
            }

        # Extract scheme_id from request data
        scheme_id = body.data.get("scheme_id")

        # Get matched schemes if available
        matched_schemes = body.data.get("matched_schemes", [])

        # Run the orchestrator
        result = await run_orchestrator(
            action=body.action,
            user_id=current_user.id,
            user_role=current_user.role,
            student_profile=student_profile,
            matched_schemes=matched_schemes,
            selected_scheme_id=scheme_id,
        )

        # Build response
        if result.get("blocked"):
            return OrchestratorResponse(
                success=False,
                action=body.action,
                blocked=True,
                block_reason=result.get("block_reason"),
                error=result.get("error"),
            )

        return OrchestratorResponse(
            success=True,
            action=body.action,
            blocked=False,
            eligibility_result=result.get("eligibility_result"),
            draft=result.get("draft"),
        )

    except PolicyBlockedError as exc:
        return OrchestratorResponse(
            success=False,
            action=body.action,
            blocked=True,
            block_reason=exc.block_reason,
            error=str(exc),
        )
    except AgentError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestrator error: {str(exc)}",
        )


# ── Health Check ─────────────────────────────────────────────────


@router.get("/health")
async def orchestrator_health():
    """Check orchestrator health."""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "graph_compiled": True,
    }
