"""
ScholarClaw — Audit Chain
Hash-chained audit logging for tamper-evident records.
Each entry links to the previous via SHA-256 hash.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from db import prisma

logger = logging.getLogger("audit.chain")

# Genesis hash for the first entry in the chain
GENESIS_HASH = "0" * 64


async def get_previous_hash(user_id: str) -> str:
    """
    Get the hash of the most recent audit entry for this user.

    Returns GENESIS_HASH if no previous entries exist.
    """
    try:
        last_entry = await prisma.auditlog.find_first(
            where={"userId": user_id},
            order={"createdAt": "desc"},
        )
        if last_entry and last_entry.previousHash:
            # Return the output hash of the last entry
            return last_entry.outputHash or GENESIS_HASH
        return GENESIS_HASH
    except Exception as exc:
        logger.warning("Failed to get previous hash: %s", exc)
        return GENESIS_HASH


def compute_entry_hash(
    user_id: str,
    action: str,
    input_hash: str,
    output_hash: str,
    agent: str,
    previous_hash: str,
    timestamp: datetime,
    metadata: dict[str, Any],
) -> str:
    """
    Compute SHA-256 hash for an audit entry.

    The hash covers all fields to ensure integrity.
    """
    entry_data = {
        "user_id": user_id,
        "action": action,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "agent": agent,
        "previous_hash": previous_hash,
        "timestamp": timestamp.isoformat(),
        "metadata": metadata,
    }
    entry_json = json.dumps(entry_data, sort_keys=True, default=str)
    return hashlib.sha256(entry_json.encode("utf-8")).hexdigest()


async def append_audit_log(
    user_id: str,
    action: str,
    input_hash: str,
    output_hash: str,
    agent: str,
    metadata: Optional[dict[str, Any]] = None,
) -> Optional[str]:
    """
    Append a new entry to the audit chain.

    Args:
        user_id: The user ID this action belongs to.
        action: The action performed (e.g., "POLICY_CHECK:check_eligibility").
        input_hash: SHA-256 hash of the input data.
        output_hash: SHA-256 hash of the output data.
        agent: The agent/component that performed the action.
        metadata: Optional additional metadata to store.

    Returns:
        The ID of the created audit log entry, or None on failure.
    """
    metadata = metadata or {}
    timestamp = datetime.now(timezone.utc)

    try:
        # Get the previous hash for chain integrity
        previous_hash = await get_previous_hash(user_id)

        # Compute entry hash
        entry_hash = compute_entry_hash(
            user_id=user_id,
            action=action,
            input_hash=input_hash,
            output_hash=output_hash,
            agent=agent,
            previous_hash=previous_hash,
            timestamp=timestamp,
            metadata=metadata,
        )

        # Store in database
        entry = await prisma.auditlog.create(
            data={
                "userId": user_id,
                "action": action,
                "inputHash": input_hash,
                "outputHash": output_hash,
                "agent": agent,
                "metadata": json.dumps(metadata),
                "previousHash": previous_hash,
                "entryHash": entry_hash,
            }
        )

        logger.debug(
            "Audit log appended: user=%s action=%s hash=%s",
            user_id,
            action,
            entry_hash[:16],
        )
        return entry.id

    except Exception as exc:
        logger.error("Failed to append audit log: %s", exc)
        return None


async def verify_chain_integrity(user_id: str) -> tuple[bool, str]:
    """
    Verify the integrity of a user's audit chain.

    Returns:
        Tuple of (is_valid, message).
    """
    try:
        entries = await prisma.auditlog.find_many(
            where={"userId": user_id},
            order={"createdAt": "asc"},
        )

        if not entries:
            return True, "No audit entries to verify"

        expected_previous = GENESIS_HASH

        for i, entry in enumerate(entries):
            # Verify chain linkage
            if entry.previousHash != expected_previous:
                return False, f"Chain break at entry {i}: expected prev={expected_previous[:16]}, got={entry.previousHash[:16] if entry.previousHash else 'None'}"

            # Recompute and verify entry hash
            metadata = json.loads(entry.metadata) if entry.metadata else {}
            computed_hash = compute_entry_hash(
                user_id=entry.userId,
                action=entry.action,
                input_hash=entry.inputHash,
                output_hash=entry.outputHash,
                agent=entry.agent,
                previous_hash=entry.previousHash or GENESIS_HASH,
                timestamp=entry.createdAt,
                metadata=metadata,
            )

            if entry.entryHash and entry.entryHash != computed_hash:
                return False, f"Hash mismatch at entry {i}: stored={entry.entryHash[:16]}, computed={computed_hash[:16]}"

            # Update expected previous for next iteration
            expected_previous = entry.outputHash or GENESIS_HASH

        return True, f"Chain verified: {len(entries)} entries"

    except Exception as exc:
        logger.error("Chain verification failed: %s", exc)
        return False, f"Verification error: {str(exc)}"
