"""
ScholarClaw — LangGraph Orchestrator
Multi-agent state machine for scholarship processing.

State flow:
START -> input_guard_node -> policy_check_node
       -> eligibility_node (if check_eligibility) -> audit_node -> output_guard_node -> END
       -> draft_node (if generate_draft) -> audit_node -> output_guard_node -> END
Any PolicyBlockedError -> audit_node (BLOCK) -> return error
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal, Optional, TypedDict

from langgraph.graph import StateGraph, END

from exceptions import PolicyBlockedError, AgentError

logger = logging.getLogger("orchestrator.graph")


# ── State Definition ─────────────────────────────────────────────


class OrchestratorState(TypedDict, total=False):
    """State for the LangGraph orchestrator."""
    # Input
    student_profile: dict[str, Any]
    matched_schemes: list[dict[str, Any]]
    selected_scheme_id: Optional[str]
    action: str  # "check_eligibility" or "generate_draft"

    # Processing
    current_step: str
    user_id: str
    user_role: str

    # Output
    eligibility_result: Optional[dict[str, Any]]
    draft: Optional[str]

    # Control flow
    error: Optional[str]
    blocked: bool
    block_reason: Optional[str]

    # Audit
    audit_entries: list[dict[str, Any]]


# ── Input Guard Node ─────────────────────────────────────────────


async def input_guard_node(state: OrchestratorState) -> OrchestratorState:
    """
    Input guard: sanitize and validate inputs.

    Checks for:
    - Required fields present
    - Input injection attempts
    - Data format validation
    """
    logger.debug("input_guard_node: validating input")
    state["current_step"] = "input_guard"

    try:
        # Validate required fields
        if not state.get("action"):
            state["error"] = "Missing required field: action"
            state["blocked"] = True
            state["block_reason"] = "Invalid input: missing action"
            return state

        valid_actions = {"check_eligibility", "generate_draft", "set_reminder"}
        if state["action"] not in valid_actions:
            state["error"] = f"Invalid action: {state['action']}"
            state["blocked"] = True
            state["block_reason"] = f"Invalid action: {state['action']}"
            return state

        # Validate user context
        if not state.get("user_id"):
            state["error"] = "Missing user context"
            state["blocked"] = True
            state["block_reason"] = "Missing authentication context"
            return state

        # Basic input sanitization for text fields
        if state.get("draft"):
            # Sanitize draft text (remove potential script injection)
            import bleach
            state["draft"] = bleach.clean(state["draft"], strip=True)

        state["blocked"] = False
        state["error"] = None
        logger.debug("input_guard_node: input validated")

    except Exception as exc:
        logger.error("input_guard_node error: %s", exc)
        state["error"] = f"Input validation error: {str(exc)}"
        state["blocked"] = True
        state["block_reason"] = "Input validation failed"

    return state


# ── Policy Check Node ────────────────────────────────────────────


async def policy_check_node(state: OrchestratorState) -> OrchestratorState:
    """
    Policy check: enforce RBAC via PolicyGate.

    Verifies the user has permission for the requested action.
    """
    logger.debug("policy_check_node: checking policy for action=%s", state.get("action"))
    state["current_step"] = "policy_check"

    if state.get("blocked"):
        return state  # Already blocked by input guard

    try:
        from policy.gate import PolicyGate

        gate = PolicyGate()
        context = {
            "user_id": state.get("user_id"),
            "student_id": state.get("user_id"),  # For own-data access
            "scheme_id": state.get("selected_scheme_id"),
        }

        decision = await gate.evaluate(
            action=state["action"],
            user_role=state.get("user_role", "user"),
            context=context,
        )

        if decision.decision == "BLOCK":
            state["blocked"] = True
            state["block_reason"] = decision.reason
            state["error"] = f"Policy blocked: {decision.reason}"
            logger.warning("policy_check_node: BLOCKED - %s", decision.reason)
        else:
            state["blocked"] = False
            logger.debug("policy_check_node: PASS")

    except PolicyBlockedError as exc:
        state["blocked"] = True
        state["block_reason"] = exc.block_reason
        state["error"] = str(exc)
    except Exception as exc:
        logger.error("policy_check_node error: %s", exc)
        state["error"] = f"Policy check error: {str(exc)}"
        state["blocked"] = True
        state["block_reason"] = "Policy check failed"

    return state


# ── Eligibility Node ─────────────────────────────────────────────


async def eligibility_node(state: OrchestratorState) -> OrchestratorState:
    """
    Eligibility check: determine if student is eligible for schemes.

    Uses Claude API with Instructor for structured output.
    """
    logger.debug("eligibility_node: checking eligibility")
    state["current_step"] = "eligibility"

    if state.get("blocked"):
        return state

    try:
        from agents.eligibility_agent import check_eligibility

        result = await check_eligibility(
            student_profile=state.get("student_profile", {}),
            scheme_id=state.get("selected_scheme_id"),
            matched_schemes=state.get("matched_schemes", []),
        )

        state["eligibility_result"] = result
        logger.debug("eligibility_node: completed with result=%s", result.get("eligible"))

    except Exception as exc:
        logger.error("eligibility_node error: %s", exc)
        state["error"] = f"Eligibility check failed: {str(exc)}"
        # Don't block on eligibility errors - allow graceful degradation

    return state


# ── Draft Generation Node ────────────────────────────────────────


async def draft_node(state: OrchestratorState) -> OrchestratorState:
    """
    Draft generation: create application draft using Claude.

    Pre-fills application with student profile and scheme details.
    """
    logger.debug("draft_node: generating draft")
    state["current_step"] = "draft"

    if state.get("blocked"):
        return state

    try:
        from agents.draft_agent import generate_draft

        draft = await generate_draft(
            student_profile=state.get("student_profile", {}),
            scheme_id=state.get("selected_scheme_id"),
            matched_schemes=state.get("matched_schemes", []),
        )

        state["draft"] = draft
        logger.debug("draft_node: completed, draft length=%d", len(draft) if draft else 0)

    except Exception as exc:
        logger.error("draft_node error: %s", exc)
        state["error"] = f"Draft generation failed: {str(exc)}"
        # Don't block on draft errors

    return state


# ── Audit Node ───────────────────────────────────────────────────


async def audit_node(state: OrchestratorState) -> OrchestratorState:
    """
    Audit logging: record the operation in the audit chain.

    Logs both successful operations and blocked attempts.
    """
    logger.debug("audit_node: logging to audit chain")
    state["current_step"] = "audit"

    try:
        from audit.chain import append_audit_log
        from audit.attack_logger import log_attack

        user_id = state.get("user_id", "unknown")
        action = state.get("action", "unknown")

        # Compute input/output hashes
        input_data = {
            "action": action,
            "scheme_id": state.get("selected_scheme_id"),
            "profile_keys": list(state.get("student_profile", {}).keys()),
        }
        input_hash = hashlib.sha256(
            json.dumps(input_data, sort_keys=True).encode()
        ).hexdigest()

        if state.get("blocked"):
            # Log as attack/violation
            await log_attack(
                event_type="ORCHESTRATOR_BLOCK",
                attacker_ip="internal",  # Would come from request context
                protection_layer="ORCHESTRATOR",
                student_id=user_id,
                block_reason=state.get("block_reason", "Unknown"),
                attack_payload=f"action={action}",
            )

            output_hash = hashlib.sha256(b"BLOCKED").hexdigest()
        else:
            # Log successful operation
            output_data = {
                "eligibility_result": state.get("eligibility_result"),
                "draft_generated": bool(state.get("draft")),
            }
            output_hash = hashlib.sha256(
                json.dumps(output_data, sort_keys=True, default=str).encode()
            ).hexdigest()

        await append_audit_log(
            user_id=user_id,
            action=f"ORCHESTRATOR:{action}",
            input_hash=input_hash,
            output_hash=output_hash,
            agent="ORCHESTRATOR",
            metadata={
                "blocked": state.get("blocked", False),
                "block_reason": state.get("block_reason"),
                "current_step": state.get("current_step"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

        # Track audit entry in state
        if "audit_entries" not in state:
            state["audit_entries"] = []
        state["audit_entries"].append({
            "action": action,
            "blocked": state.get("blocked", False),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    except Exception as exc:
        logger.error("audit_node error: %s", exc)
        # Don't fail the operation if audit fails

    return state


# ── Output Guard Node ────────────────────────────────────────────


async def output_guard_node(state: OrchestratorState) -> OrchestratorState:
    """
    Output guard: sanitize and validate outputs.

    Ensures no sensitive data leaks and output is safe.
    """
    logger.debug("output_guard_node: validating output")
    state["current_step"] = "output_guard"

    if state.get("blocked"):
        # Clear any partial results on blocked operations
        state["eligibility_result"] = None
        state["draft"] = None
        return state

    try:
        import bleach

        # Sanitize draft output if present
        if state.get("draft"):
            state["draft"] = bleach.clean(
                state["draft"],
                tags=["p", "br", "strong", "em", "ul", "ol", "li"],
                strip=True,
            )

        # Ensure no internal fields leak to output
        # (These are filtered in router before returning to client)

        logger.debug("output_guard_node: output validated")

    except Exception as exc:
        logger.error("output_guard_node error: %s", exc)
        # Don't fail on output guard errors

    return state


# ── Conditional Edge Functions ───────────────────────────────────


def route_after_policy_check(state: OrchestratorState) -> str:
    """
    Route after policy check based on action type.

    Returns the next node name.
    """
    if state.get("blocked"):
        return "audit"  # Go directly to audit for blocked requests

    action = state.get("action", "")

    if action == "check_eligibility":
        return "eligibility"
    elif action == "generate_draft":
        return "draft_gen"
    elif action == "set_reminder":
        return "audit"  # Reminders are handled separately
    else:
        return "audit"  # Unknown action, just audit and finish


def route_after_eligibility(state: OrchestratorState) -> str:
    """Route after eligibility check."""
    return "audit"


def route_after_draft(state: OrchestratorState) -> str:
    """Route after draft generation."""
    return "audit"


def route_after_audit(state: OrchestratorState) -> str:
    """Route after audit - go to output guard."""
    return "output_guard"


# ── Graph Builder ────────────────────────────────────────────────


def build_orchestrator_graph() -> StateGraph:
    """
    Build and compile the LangGraph orchestrator.

    Flow:
    START -> input_guard -> policy_check
          -> eligibility (if check_eligibility) -> audit -> output_guard -> END
          -> draft (if generate_draft) -> audit -> output_guard -> END
          -> audit (if blocked) -> output_guard -> END
    """
    # Create the graph
    builder = StateGraph(OrchestratorState)

    # Add nodes
    builder.add_node("input_guard", input_guard_node)
    builder.add_node("policy_check", policy_check_node)
    builder.add_node("eligibility", eligibility_node)
    builder.add_node("draft_gen", draft_node)
    builder.add_node("audit", audit_node)
    builder.add_node("output_guard", output_guard_node)

    # Set entry point
    builder.set_entry_point("input_guard")

    # Add edges
    builder.add_edge("input_guard", "policy_check")

    # Conditional routing after policy check
    builder.add_conditional_edges(
        "policy_check",
        route_after_policy_check,
        {
            "eligibility": "eligibility",
            "draft_gen": "draft_gen",
            "audit": "audit",
        },
    )

    # Eligibility -> audit
    builder.add_edge("eligibility", "audit")

    # Draft -> audit
    builder.add_edge("draft_gen", "audit")

    # Audit -> output_guard
    builder.add_edge("audit", "output_guard")

    # Output guard -> END
    builder.add_edge("output_guard", END)

    return builder


# ── Compiled Graph ───────────────────────────────────────────────

# Build the graph at module load
_graph_builder = build_orchestrator_graph()
orchestrator_graph = _graph_builder.compile()


# ── Public Interface ─────────────────────────────────────────────


async def run_orchestrator(
    action: str,
    user_id: str,
    user_role: str = "user",
    student_profile: Optional[dict] = None,
    matched_schemes: Optional[list] = None,
    selected_scheme_id: Optional[str] = None,
) -> dict[str, Any]:
    """
    Run the orchestrator graph with the given inputs.

    Args:
        action: The action to perform ("check_eligibility" or "generate_draft").
        user_id: The authenticated user's ID.
        user_role: The user's role ("user", "student", or "admin").
        student_profile: Optional student profile data.
        matched_schemes: Optional list of matched schemes.
        selected_scheme_id: Optional specific scheme ID to check.

    Returns:
        The final state after graph execution.
    """
    initial_state: OrchestratorState = {
        "action": action,
        "user_id": user_id,
        "user_role": user_role,
        "student_profile": student_profile or {},
        "matched_schemes": matched_schemes or [],
        "selected_scheme_id": selected_scheme_id,
        "current_step": "init",
        "eligibility_result": None,
        "draft": None,
        "error": None,
        "blocked": False,
        "block_reason": None,
        "audit_entries": [],
    }

    logger.info(
        "Running orchestrator: action=%s user=%s scheme=%s",
        action,
        user_id,
        selected_scheme_id,
    )

    try:
        # Run the graph
        final_state = await orchestrator_graph.ainvoke(initial_state)

        logger.info(
            "Orchestrator completed: blocked=%s step=%s",
            final_state.get("blocked"),
            final_state.get("current_step"),
        )

        return dict(final_state)

    except Exception as exc:
        logger.error("Orchestrator failed: %s", exc)
        raise AgentError(f"Orchestrator execution failed: {str(exc)}")
