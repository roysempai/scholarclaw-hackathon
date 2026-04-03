"""
ScholarClaw — Attack Logger
Logs security incidents and policy violations for visibility.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from db import prisma

logger = logging.getLogger("audit.attack_logger")


async def log_attack(
    event_type: str,
    attacker_ip: str,
    protection_layer: str,
    student_id: Optional[str] = None,
    block_reason: Optional[str] = None,
    attack_payload: Optional[str] = None,
) -> Optional[str]:
    """
    Log a security incident or attack attempt.

    Args:
        event_type: Type of event (e.g., "POLICY_VIOLATION", "INJECTION_ATTEMPT").
        attacker_ip: IP address of the attacker.
        protection_layer: Which layer detected/blocked the attack
                          (e.g., "POLICY_GATE", "INPUT_GUARD", "ARMORIQ").
        student_id: Optional student ID involved in the incident.
        block_reason: Human-readable reason for the block.
        attack_payload: The malicious payload or action attempted.

    Returns:
        The ID of the created attack log entry, or None on failure.
    """
    timestamp = datetime.now(timezone.utc)

    try:
        entry = await prisma.attacklog.create(
            data={
                "timestamp": timestamp,
                "eventType": event_type,
                "attackerIp": attacker_ip,
                "protectionLayer": protection_layer,
                "studentId": student_id,
                "blockReason": block_reason or "",
                "attackPayload": attack_payload or "",
            }
        )

        logger.warning(
            "ATTACK LOGGED: type=%s ip=%s layer=%s reason=%s",
            event_type,
            attacker_ip,
            protection_layer,
            block_reason,
        )

        return entry.id

    except Exception as exc:
        logger.error("Failed to log attack: %s", exc)
        return None


async def get_recent_attacks(
    limit: int = 50,
    event_type: Optional[str] = None,
    student_id: Optional[str] = None,
) -> list[dict]:
    """
    Retrieve recent attack logs with optional filtering.

    Args:
        limit: Maximum number of entries to return.
        event_type: Optional filter by event type.
        student_id: Optional filter by student ID.

    Returns:
        List of attack log entries as dictionaries.
    """
    try:
        where_clause: dict = {}
        if event_type:
            where_clause["eventType"] = event_type
        if student_id:
            where_clause["studentId"] = student_id

        entries = await prisma.attacklog.find_many(
            where=where_clause if where_clause else None,
            order={"timestamp": "desc"},
            take=limit,
        )

        return [
            {
                "id": entry.id,
                "timestamp": entry.timestamp.isoformat(),
                "event_type": entry.eventType,
                "attacker_ip": entry.attackerIp,
                "protection_layer": entry.protectionLayer,
                "student_id": entry.studentId,
                "block_reason": entry.blockReason,
                "attack_payload": entry.attackPayload,
            }
            for entry in entries
        ]

    except Exception as exc:
        logger.error("Failed to retrieve attack logs: %s", exc)
        return []


async def get_attack_stats(days: int = 7) -> dict:
    """
    Get attack statistics for the specified period.

    Returns counts by event type and protection layer.
    """
    from datetime import timedelta

    try:
        since = datetime.now(timezone.utc) - timedelta(days=days)

        entries = await prisma.attacklog.find_many(
            where={"timestamp": {"gte": since}},
        )

        # Aggregate stats
        by_type: dict[str, int] = {}
        by_layer: dict[str, int] = {}

        for entry in entries:
            by_type[entry.eventType] = by_type.get(entry.eventType, 0) + 1
            by_layer[entry.protectionLayer] = by_layer.get(entry.protectionLayer, 0) + 1

        return {
            "total": len(entries),
            "period_days": days,
            "by_event_type": by_type,
            "by_protection_layer": by_layer,
        }

    except Exception as exc:
        logger.error("Failed to get attack stats: %s", exc)
        return {"total": 0, "period_days": days, "by_event_type": {}, "by_protection_layer": {}}
