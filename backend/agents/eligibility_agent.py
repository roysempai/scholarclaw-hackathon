"""
ScholarClaw — Eligibility Agent
Checks student eligibility for scholarship schemes using Claude.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from config import settings

logger = logging.getLogger("agents.eligibility")


# ── Structured Output Models ─────────────────────────────────────


class EligibilityResult(BaseModel):
    """Structured eligibility check result."""
    eligible: bool = Field(description="Whether the student is eligible for the scheme")
    score: float = Field(description="Eligibility score from 0.0 to 1.0", ge=0.0, le=1.0)
    missing_fields: list[str] = Field(
        default_factory=list,
        description="List of missing or incomplete profile fields"
    )
    matched_criteria: list[str] = Field(
        default_factory=list,
        description="List of eligibility criteria that were matched"
    )
    unmatched_criteria: list[str] = Field(
        default_factory=list,
        description="List of eligibility criteria that were not matched"
    )
    reasoning: str = Field(description="Explanation of the eligibility determination")


# ── Eligibility Check Function ───────────────────────────────────


async def check_eligibility(
    student_profile: dict[str, Any],
    scheme_id: Optional[str] = None,
    matched_schemes: Optional[list[dict]] = None,
) -> dict[str, Any]:
    """
    Check student eligibility for a scholarship scheme.

    Uses Claude API with Instructor for structured output.

    Args:
        student_profile: The student's profile data.
        scheme_id: Optional specific scheme ID to check against.
        matched_schemes: Optional list of pre-matched schemes.

    Returns:
        Dictionary with eligibility result including:
        - eligible: bool
        - score: float (0.0-1.0)
        - missing_fields: list[str]
        - matched_criteria: list[str]
        - unmatched_criteria: list[str]
        - reasoning: str
    """
    logger.debug("check_eligibility: scheme_id=%s", scheme_id)

    # Get scheme details
    scheme = None
    if scheme_id:
        scheme = await _get_scheme(scheme_id)
    elif matched_schemes:
        # Use the first matched scheme if no specific ID
        scheme = matched_schemes[0] if matched_schemes else None

    if not scheme:
        logger.warning("No scheme found for eligibility check")
        return {
            "eligible": False,
            "score": 0.0,
            "missing_fields": ["scheme_not_found"],
            "matched_criteria": [],
            "unmatched_criteria": [],
            "reasoning": "No scheme found to check eligibility against.",
        }

    # Check if Groq API is available
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — using rule-based eligibility")
        return await _rule_based_eligibility(student_profile, scheme)

    try:
        return await _llm_eligibility_check(student_profile, scheme)
    except Exception as exc:
        logger.error("LLM eligibility check failed: %s", exc)
        # Fall back to rule-based check
        return await _rule_based_eligibility(student_profile, scheme)


async def _get_scheme(scheme_id: str) -> Optional[dict]:
    """Fetch scheme details from database."""
    try:
        from db import prisma
        scheme = await prisma.scholarshipscheme.find_unique(where={"id": scheme_id})
        if scheme:
            return {
                "id": scheme.id,
                "name": scheme.name,
                "provider": scheme.provider,
                "description": scheme.description,
                "amount": scheme.amount,
                "deadline": scheme.deadline.isoformat() if scheme.deadline else None,
                "eligibility_criteria": scheme.eligibilityCriteria,
                "required_documents": scheme.requiredDocuments,
            }
    except Exception as exc:
        logger.warning("Failed to fetch scheme %s: %s", scheme_id, exc)
    return None


async def _llm_eligibility_check(
    student_profile: dict[str, Any],
    scheme: dict[str, Any],
) -> dict[str, Any]:
    """
    Check eligibility using Groq API with LLaMA model.
    """
    from groq import Groq
    import json as json_module

    client = Groq(api_key=settings.GROQ_API_KEY)

    # Build the prompt
    prompt = f"""You are an eligibility checker for scholarship schemes. Respond ONLY with valid JSON.

STUDENT PROFILE:
{_format_profile(student_profile)}

SCHOLARSHIP SCHEME:
Name: {scheme.get('name', 'Unknown')}
Provider: {scheme.get('provider', 'Unknown')}
Description: {scheme.get('description', 'No description')}
Amount: {scheme.get('amount', 'Unknown')}
Eligibility Criteria: {scheme.get('eligibility_criteria', 'Not specified')}

TASK:
1. Compare the student profile against the eligibility criteria
2. Determine if the student is eligible (true/false)
3. Calculate an eligibility score (0.0 to 1.0)
4. List any missing profile fields that would help determine eligibility
5. List which criteria are matched and which are not matched
6. Provide a clear reasoning for your determination

Be thorough but fair. If criteria are ambiguous, give the student the benefit of the doubt.

Respond with this exact JSON structure:
{{"eligible": true/false, "score": 0.0-1.0, "missing_fields": [], "matched_criteria": [], "unmatched_criteria": [], "reasoning": "explanation"}}"""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.1,
    )

    # Parse the response
    content = response.choices[0].message.content.strip()

    # Try to extract JSON from the response
    try:
        # Handle potential markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json_module.loads(content)
        return {
            "eligible": result.get("eligible", False),
            "score": float(result.get("score", 0.0)),
            "missing_fields": result.get("missing_fields", []),
            "matched_criteria": result.get("matched_criteria", []),
            "unmatched_criteria": result.get("unmatched_criteria", []),
            "reasoning": result.get("reasoning", "No reasoning provided"),
        }
    except json_module.JSONDecodeError:
        logger.warning("Failed to parse LLM response as JSON, using rule-based fallback")
        return await _rule_based_eligibility(student_profile, scheme)


async def _rule_based_eligibility(
    student_profile: dict[str, Any],
    scheme: dict[str, Any],
) -> dict[str, Any]:
    """
    Simple rule-based eligibility check (fallback when Claude unavailable).
    """
    matched = []
    unmatched = []
    missing = []

    # Check common criteria
    criteria = scheme.get("eligibility_criteria", "")
    if isinstance(criteria, str):
        criteria = criteria.lower()

    # Category check
    category = student_profile.get("category", "").upper()
    if category:
        if "sc" in criteria and category == "SC":
            matched.append("Category: SC")
        elif "st" in criteria and category == "ST":
            matched.append("Category: ST")
        elif "obc" in criteria and category == "OBC":
            matched.append("Category: OBC")
        elif "general" in criteria or "gen" in criteria:
            matched.append("Category: General")
    else:
        missing.append("category")

    # Income check
    income = student_profile.get("income") or student_profile.get("annualIncome")
    if income:
        # Simple income threshold check
        if income <= 250000:
            matched.append("Income: Below 2.5L")
        elif income <= 500000:
            matched.append("Income: Below 5L")
    else:
        missing.append("income")

    # State check
    state = student_profile.get("state", "")
    if state:
        matched.append(f"State: {state}")
    else:
        missing.append("state")

    # Marks check
    marks = student_profile.get("marks_12th") or student_profile.get("percentage")
    if marks:
        if marks >= 60:
            matched.append(f"Marks: {marks}%")
    else:
        missing.append("marks_12th")

    # Calculate score
    total_checks = len(matched) + len(unmatched)
    score = len(matched) / max(total_checks, 1)

    # Determine eligibility
    eligible = len(matched) >= 2 and len(missing) <= 2

    return {
        "eligible": eligible,
        "score": round(score, 2),
        "missing_fields": missing,
        "matched_criteria": matched,
        "unmatched_criteria": unmatched,
        "reasoning": f"Rule-based check: {len(matched)} criteria matched, {len(missing)} fields missing.",
    }


def _format_profile(profile: dict[str, Any]) -> str:
    """Format student profile for prompt."""
    lines = []
    field_map = {
        "name": "Name",
        "category": "Category",
        "income": "Annual Income",
        "annualIncome": "Annual Income",
        "state": "State",
        "course": "Course",
        "year": "Year of Study",
        "marks_12th": "12th Marks (%)",
        "percentage": "Percentage",
        "educationLevel": "Education Level",
    }

    for key, label in field_map.items():
        if key in profile and profile[key]:
            lines.append(f"- {label}: {profile[key]}")

    return "\n".join(lines) if lines else "- No profile data available"
