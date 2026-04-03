"""
ScholarClaw — Draft Agent
Generates application drafts using Claude.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from config import settings

logger = logging.getLogger("agents.draft")


# ── Structured Output Models ─────────────────────────────────────


class ApplicationDraft(BaseModel):
    """Structured application draft."""
    personal_statement: str = Field(
        description="Personal statement section of the application"
    )
    academic_achievements: str = Field(
        description="Academic achievements section"
    )
    financial_need_statement: str = Field(
        description="Statement of financial need"
    )
    future_goals: str = Field(
        description="Future academic and career goals"
    )
    additional_information: str = Field(
        default="",
        description="Any additional relevant information"
    )


# ── Draft Generation Function ────────────────────────────────────


async def generate_draft(
    student_profile: dict[str, Any],
    scheme_id: Optional[str] = None,
    matched_schemes: Optional[list[dict]] = None,
) -> str:
    """
    Generate an application draft for a scholarship.

    Uses Claude API with Instructor for structured output.

    Args:
        student_profile: The student's profile data.
        scheme_id: Optional specific scheme ID to draft for.
        matched_schemes: Optional list of pre-matched schemes.

    Returns:
        Generated draft text.
    """
    logger.debug("generate_draft: scheme_id=%s", scheme_id)

    # Get scheme details
    scheme = None
    if scheme_id:
        scheme = await _get_scheme(scheme_id)
    elif matched_schemes:
        scheme = matched_schemes[0] if matched_schemes else None

    if not scheme:
        logger.warning("No scheme found for draft generation")
        return _generate_generic_draft(student_profile)

    # Check if Groq API is available
    if not settings.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not set — using template-based draft")
        return _generate_template_draft(student_profile, scheme)

    try:
        return await _llm_draft_generation(student_profile, scheme)
    except Exception as exc:
        logger.error("LLM draft generation failed: %s", exc)
        return _generate_template_draft(student_profile, scheme)


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


async def _llm_draft_generation(
    student_profile: dict[str, Any],
    scheme: dict[str, Any],
) -> str:
    """
    Generate draft using Groq API with LLaMA model.
    """
    from groq import Groq

    client = Groq(api_key=settings.GROQ_API_KEY)

    # Extract student name
    student_name = student_profile.get("name", "the applicant")

    prompt = f"""You are a scholarship application assistant helping a student draft their application.

STUDENT PROFILE:
{_format_profile(student_profile)}

SCHOLARSHIP DETAILS:
Name: {scheme.get('name', 'Unknown')}
Provider: {scheme.get('provider', 'Unknown')}
Description: {scheme.get('description', 'No description')}
Amount: {scheme.get('amount', 'Unknown')}
Eligibility: {scheme.get('eligibility_criteria', 'Not specified')}
Required Documents: {scheme.get('required_documents', 'Not specified')}

TASK:
Generate a professional scholarship application draft for {student_name}. The draft should include:

1. **Personal Statement** (2-3 paragraphs): Introduce the student and their background
2. **Academic Achievements**: Highlight their academic accomplishments based on the profile
3. **Statement of Financial Need**: Craft a dignified statement about financial circumstances
4. **Future Goals**: Describe their academic and career aspirations
5. **Additional Information**: Include any other relevant details

Guidelines:
- Be professional but personal
- Use specific details from the profile
- Align the application with the scholarship's focus
- Be honest and authentic
- Keep each section concise but impactful

Format the response with clear section headers using markdown (## for headers)."""

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2048,
        temperature=0.7,
    )

    content = response.choices[0].message.content.strip()

    # Add title if not present
    if not content.startswith("#"):
        content = f"# Application for {scheme.get('name', 'Scholarship')}\n\n{content}"

    return content


def _format_draft(draft: ApplicationDraft, scheme_name: str) -> str:
    """Format the structured draft into final text."""
    sections = [
        f"# Application for {scheme_name}",
        "",
        "## Personal Statement",
        draft.personal_statement,
        "",
        "## Academic Achievements",
        draft.academic_achievements,
        "",
        "## Statement of Financial Need",
        draft.financial_need_statement,
        "",
        "## Future Goals",
        draft.future_goals,
    ]

    if draft.additional_information:
        sections.extend([
            "",
            "## Additional Information",
            draft.additional_information,
        ])

    return "\n".join(sections)


def _generate_template_draft(
    student_profile: dict[str, Any],
    scheme: dict[str, Any],
) -> str:
    """
    Generate a template-based draft (fallback when Claude unavailable).
    """
    name = student_profile.get("name", "[Your Name]")
    course = student_profile.get("course", "[Your Course]")
    year = student_profile.get("year", "[Year]")
    state = student_profile.get("state", "[State]")
    income = student_profile.get("income") or student_profile.get("annualIncome", "[Income]")
    marks = student_profile.get("marks_12th") or student_profile.get("percentage", "[Marks]")
    scheme_name = scheme.get("name", "this scholarship")

    return f"""# Application for {scheme_name}

## Personal Statement

My name is {name}, and I am currently pursuing {course} in year {year}. I am writing to apply for {scheme_name} as I believe my academic dedication and personal circumstances make me a suitable candidate for this opportunity.

Coming from {state}, I have always valued education as a pathway to a better future. My journey has been shaped by both opportunities and challenges, which have strengthened my resolve to succeed academically and contribute meaningfully to society.

## Academic Achievements

I have maintained consistent academic performance throughout my educational journey:
- 12th Standard: {marks}%
- Currently studying: {course}, Year {year}

I am committed to maintaining high academic standards and continuously improving my knowledge and skills in my chosen field.

## Statement of Financial Need

My family's annual income is approximately Rs. {income}. While my family has always prioritized my education, financial constraints sometimes make it challenging to meet all educational expenses. This scholarship would significantly ease the financial burden and allow me to focus more on my studies and extracurricular activities.

## Future Goals

Upon completing my education, I aspire to:
1. Excel in my chosen field of study
2. Contribute to my community and society at large
3. Support my family and help create opportunities for others facing similar circumstances

I am committed to making the most of every opportunity and working hard to achieve these goals.

---

*Note: This is a draft template. Please personalize it with specific details, achievements, and experiences.*
"""


def _generate_generic_draft(student_profile: dict[str, Any]) -> str:
    """Generate a generic draft when no scheme is specified."""
    return _generate_template_draft(student_profile, {"name": "Scholarship Application"})


def _format_profile(profile: dict[str, Any]) -> str:
    """Format student profile for prompt."""
    lines = []
    field_map = {
        "name": "Name",
        "category": "Category",
        "income": "Annual Income (Rs.)",
        "annualIncome": "Annual Income (Rs.)",
        "state": "State",
        "course": "Course",
        "year": "Year of Study",
        "marks_12th": "12th Marks (%)",
        "percentage": "Percentage",
        "educationLevel": "Education Level",
        "reg_number": "Registration Number",
        "institution": "Institution",
    }

    for key, label in field_map.items():
        if key in profile and profile[key]:
            lines.append(f"- {label}: {profile[key]}")

    return "\n".join(lines) if lines else "- No profile data available"
