"""
ScholarClaw — Policy Gate
Role-Based Access Control (RBAC) enforcement for agent actions.

This module implements the PolicyGate that evaluates whether a user
has permission to perform a specific action based on their role.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from audit.attack_logger import log_attack
from exceptions import PolicyBlockedError

logger = logging.getLogger("policy.gate")


# ── Decision Types ──────────────────────────────────────────────

class Decision(str, Enum):
    """Policy decision types."""
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


@dataclass
class PolicyDecision:
    """Result of a policy evaluation."""
    decision: Decision
    reason: str
    action: str
    user_role: str


# ── Policy Rules ────────────────────────────────────────────────

# Actions allowed for each role (case-insensitive role matching)
POLICY_RULES: dict[str, set[str]] = {
    "STUDENT": {
        "check_eligibility",
        "generate_draft",
        "set_reminder",
        "view_own_profile",
        "update_own_profile",
        "view_own_applications",
        "view_schemes",
    },
    "ADMIN": {
        # Admins have all student permissions plus admin actions
        "check_eligibility",
        "generate_draft",
        "set_reminder",
        "view_own_profile",
        "update_own_profile",
        "view_own_applications",
        "view_schemes",
        # Admin-specific actions
        "manage_users",
        "view_all_profiles",
        "view_audit_logs",
        "view_attack_logs",
        "manage_schemes",
        "verify_chain",
    },
}

# Actions that are always blocked (security-sensitive)
BLOCKED_ACTIONS: set[str] = {
    "delete_all_data",
    "bypass_policy",
    "execute_raw_sql",
    "modify_audit_chain",
}


# ── Policy Gate ─────────────────────────────────────────────────

class PolicyGate:
    """
    Policy enforcement gate for RBAC.

    Evaluates whether a user with a given role can perform an action.
    Logs violations to the attack log.
    """

    def __init__(self):
        self.rules = POLICY_RULES
        self.blocked_actions = BLOCKED_ACTIONS

    async def evaluate(
        self,
        action: str,
        user_role: str,
        context: Optional[dict[str, Any]] = None,
    ) -> PolicyDecision:
        """
        Evaluate if the action is allowed for the given role.

        Args:
            action: The action being attempted.
            user_role: The user's role (e.g., "STUDENT", "ADMIN").
            context: Optional context for the evaluation (user_id, resource_id, etc.).

        Returns:
            PolicyDecision with ALLOW or BLOCK.
        """
        context = context or {}
        normalized_role = user_role.upper()
        normalized_action = action.lower()

        logger.debug(
            "Evaluating policy: action=%s role=%s",
            normalized_action,
            normalized_role,
        )

        # Check if action is always blocked
        if normalized_action in self.blocked_actions:
            decision = PolicyDecision(
                decision=Decision.BLOCK,
                reason=f"Action '{action}' is not permitted",
                action=action,
                user_role=user_role,
            )
            await self._log_violation(decision, context)
            return decision

        # Get allowed actions for the role
        allowed_actions = self.rules.get(normalized_role, set())

        # Check if action is allowed for this role
        if normalized_action in allowed_actions:
            logger.debug("Policy ALLOW: %s can perform %s", normalized_role, action)
            return PolicyDecision(
                decision=Decision.ALLOW,
                reason="Action permitted",
                action=action,
                user_role=user_role,
            )

        # Action not allowed - block
        decision = PolicyDecision(
            decision=Decision.BLOCK,
            reason=f"Role '{user_role}' is not authorized for action '{action}'",
            action=action,
            user_role=user_role,
        )
        await self._log_violation(decision, context)
        return decision

    async def _log_violation(
        self,
        decision: PolicyDecision,
        context: dict[str, Any],
    ) -> None:
        """Log a policy violation to the attack log."""
        logger.warning(
            "POLICY VIOLATION: role=%s action=%s reason=%s",
            decision.user_role,
            decision.action,
            decision.reason,
        )

        await log_attack(
            event_type="POLICY_VIOLATION",
            attacker_ip=context.get("client_ip", "unknown"),
            protection_layer="POLICY_GATE",
            student_id=context.get("user_id"),
            block_reason=decision.reason,
            attack_payload=f"action={decision.action}, role={decision.user_role}",
        )

    def check_or_raise(
        self,
        action: str,
        user_role: str,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Synchronous check that raises PolicyBlockedError if blocked.

        Use this for simple sync checks where you don't need async.
        Note: This does NOT log violations (use evaluate() for that).
        """
        context = context or {}
        normalized_role = user_role.upper()
        normalized_action = action.lower()

        # Check blocked actions
        if normalized_action in self.blocked_actions:
            raise PolicyBlockedError(
                detail=f"Action '{action}' is not permitted",
                block_reason=f"Blocked action: {action}",
            )

        # Check role permissions
        allowed_actions = self.rules.get(normalized_role, set())
        if normalized_action not in allowed_actions:
            raise PolicyBlockedError(
                detail=f"Role '{user_role}' is not authorized for action '{action}'",
                block_reason=f"Unauthorized: {user_role} cannot {action}",
            )


# ── Singleton Instance ──────────────────────────────────────────

_policy_gate: Optional[PolicyGate] = None


def get_policy_gate() -> PolicyGate:
    """Get or create the singleton PolicyGate instance."""
    global _policy_gate
    if _policy_gate is None:
        _policy_gate = PolicyGate()
    return _policy_gate
