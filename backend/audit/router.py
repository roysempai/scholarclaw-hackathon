"""
ScholarClaw — Audit Router
Hash-chained audit logging endpoints.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from db import prisma
from dependencies import get_current_user, CurrentUser
from audit.chain import append_audit_log, verify_chain_integrity, GENESIS_HASH

router = APIRouter(prefix="/api/audit", tags=["Audit"])


# ── Schemas ─────────────────────────────────────────────────────

class AuditResult(str):
    """Result of an audited action."""
    PASS = "PASS"
    BLOCK = "BLOCK"


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry (internal use)."""
    action: str = Field(..., min_length=1, max_length=200)
    result: str  # PASS or BLOCK
    block_reason: Optional[str] = Field(None, max_length=500)
    agent: Optional[str] = Field(None, max_length=100)
    input_data: Optional[str] = Field(None, description="Raw input to hash")
    output_data: Optional[str] = Field(None, description="Raw output to hash")
    metadata: Optional[dict[str, Any]] = None

    class Config:
        extra = "forbid"


class AuditLogEntry(BaseModel):
    """Schema for audit log entry response."""
    id: str
    user_id: Optional[str] = None
    action: str
    result: Optional[str] = None
    block_reason: Optional[str] = None
    agent: Optional[str] = None
    input_hash: str
    output_hash: str
    previous_hash: str
    current_hash: str
    metadata: Optional[dict[str, Any]] = None
    event_type: Optional[str] = None
    attacker_ip: Optional[str] = None
    attack_payload: Optional[str] = None
    protection_layer: Optional[str] = None
    created_at: datetime


class AuditLogList(BaseModel):
    """Schema for paginated audit log list."""
    logs: list[AuditLogEntry]
    total: int
    limit: int
    offset: int


class ChainVerifyResponse(BaseModel):
    """Schema for chain verification response."""
    valid: bool
    total_entries: int
    message: str


class AttackLogEntry(BaseModel):
    """Schema for attack log entry (from audit log)."""
    id: str
    timestamp: str
    event_type: str
    attacker_ip: Optional[str] = None
    protection_layer: Optional[str] = None
    block_reason: Optional[str] = None
    attack_payload: Optional[str] = None
    student_id: Optional[str] = None
    blocked: bool = True

    class Config:
        extra = "forbid"


class AttackLogList(BaseModel):
    """Schema for attack log list response."""
    attacks: list[AttackLogEntry]
    total: int


class AttackSummary(BaseModel):
    """Schema for attack summary statistics (24h window)."""
    total_attacks_24h: int
    by_type: dict[str, int]
    by_layer: dict[str, int]
    top_attacker_ips: list[dict]


# ── Helper: Require Admin Role ──────────────────────────────────

def require_admin(current_user: CurrentUser):
    """Check if user has admin role (case-insensitive)."""
    if current_user.role.upper() != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role 'admin' required. You have '{current_user.role}'.",
        )
    return current_user


# ── Create Audit Log ────────────────────────────────────────────

@router.post("/log", response_model=AuditLogEntry, status_code=status.HTTP_201_CREATED)
async def create_audit_log(
    body: AuditLogCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Create a new audit log entry (internal use by agents).

    The entry is automatically chained to the user's previous entries
    using SHA-256 hashing for tamper detection.
    """
    # Hash input and output data
    input_hash = hashlib.sha256(
        (body.input_data or "").encode("utf-8")
    ).hexdigest()
    output_hash = hashlib.sha256(
        (body.output_data or "").encode("utf-8")
    ).hexdigest()

    # Append to audit chain
    entry_id = await append_audit_log(
        user_id=current_user.id,
        action=body.action,
        input_hash=input_hash,
        output_hash=output_hash,
        agent=body.agent or "system",
        metadata=body.metadata,
    )

    if not entry_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create audit log entry",
        )

    # Fetch the created entry
    entry = await prisma.auditlog.find_unique(where={"id": entry_id})

    return AuditLogEntry(
        id=entry.id,
        user_id=entry.userId,
        action=entry.action,
        result=body.result,
        block_reason=body.block_reason,
        agent=entry.agent,
        input_hash=entry.inputHash,
        output_hash=entry.outputHash,
        previous_hash=entry.previousHash or GENESIS_HASH,
        current_hash=entry.entryHash or "",
        metadata=json.loads(entry.metadata) if entry.metadata else None,
        created_at=entry.createdAt,
    )


# ── Get My Audit Logs ───────────────────────────────────────────

@router.get("/logs", response_model=AuditLogList)
async def get_my_audit_logs(
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Get audit logs for the authenticated user.

    Returns only the calling user's logs, paginated.
    """
    try:
        # Get total count
        total = await prisma.auditlog.count(where={"userId": current_user.id})

        # Get logs
        logs = await prisma.auditlog.find_many(
            where={"userId": current_user.id},
            order={"createdAt": "desc"},
            take=limit,
            skip=offset,
        )

        entries = []
        for log in logs:
            try:
                metadata = json.loads(log.metadata) if log.metadata else None
            except (json.JSONDecodeError, TypeError):
                metadata = None

            entries.append(AuditLogEntry(
                id=log.id,
                user_id=log.userId,
                action=log.action,
                result=metadata.get("result") if metadata else None,
                block_reason=metadata.get("block_reason") if metadata else None,
                agent=log.agent,
                input_hash=log.inputHash,
                output_hash=log.outputHash,
                previous_hash=log.previousHash or GENESIS_HASH,
                current_hash=log.entryHash or "",
                metadata=metadata,
                event_type=metadata.get("event_type") if metadata else None,
                attacker_ip=metadata.get("attacker_ip") if metadata else None,
                attack_payload=metadata.get("attack_payload") if metadata else None,
                protection_layer=metadata.get("protection_layer") if metadata else None,
                created_at=log.createdAt,
            ))

        return AuditLogList(
            logs=entries,
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        import logging
        logging.getLogger("audit.router").error(f"Error getting audit logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Verify Chain Integrity ──────────────────────────────────────

@router.get("/verify", response_model=ChainVerifyResponse)
async def verify_audit_chain(
    current_user: CurrentUser = Depends(get_current_user),
    user_id: Optional[str] = Query(
        None, description="User ID to verify (admin can verify any user)"
    ),
):
    """
    Verify the integrity of the audit chain.

    Admin only. Recomputes all hashes and checks chain linkage.
    If user_id is not provided, verifies the calling admin's chain.
    """
    require_admin(current_user)

    target_user_id = user_id or current_user.id

    is_valid, message = await verify_chain_integrity(target_user_id)

    # Get total entries
    total = await prisma.auditlog.count(where={"userId": target_user_id})

    return ChainVerifyResponse(
        valid=is_valid,
        total_entries=total,
        message=message,
    )


# ── Get Attack Logs (Admin Only) ────────────────────────────────

@router.get("/attacks", response_model=AttackLogList)
async def get_attack_logs(
    current_user: CurrentUser = Depends(get_current_user),
    limit: int = Query(100, ge=1, le=100),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
):
    """
    Get all BLOCK events where result='BLOCK' and event_type != 'USER_ACTION'.

    Admin only. Returns security events from all protection layers:
    - RATE_LIMIT_EXCEEDED: Request rate exceeded
    - JWT_INVALID: Invalid/forged JWT token
    - PROMPT_INJECTION: Detected injection attack
    - POLICY_VIOLATION: Unauthorized action attempt

    Response fields:
    - timestamp: When the attack was detected
    - event_type: Category of attack
    - attacker_ip: Source IP address
    - protection_layer: Which layer blocked (RATE_LIMITER, JWT_GUARD, ARMORIQ, POLICY_GATE)
    - block_reason: Human-readable explanation
    - attack_payload: Fingerprinted payload (never raw)
    """
    require_admin(current_user)

    # Try to get from AttackLog table, fall back to empty list if table doesn't exist
    try:
        # Build query filters
        where_clause = {}
        if event_type:
            where_clause["eventType"] = event_type

        # Get attacks from AttackLog table
        attacks = await prisma.attacklog.find_many(
            where=where_clause,
            order={"timestamp": "desc"},
            take=limit,
        )

        total = await prisma.attacklog.count(where=where_clause)

        entries = []
        for attack in attacks:
            entries.append(AttackLogEntry(
                id=attack.id,
                timestamp=attack.timestamp.isoformat(),
                event_type=attack.eventType,
                attacker_ip=attack.attackerIp,
                protection_layer=attack.protectionLayer,
                block_reason=attack.blockReason,
                attack_payload=attack.attackPayload,
                student_id=attack.studentId,
                blocked=True,
            ))

        return AttackLogList(
            attacks=entries,
            total=total,
        )
    except AttributeError:
        # AttackLog table doesn't exist in Prisma client
        # Return empty list - table needs to be migrated
        return AttackLogList(attacks=[], total=0)


# ── Attack Summary (Admin Only) ─────────────────────────────────

@router.get("/attack-summary", response_model=AttackSummary)
async def get_attack_summary(
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Get summary statistics for attack events in the last 24 hours.

    Admin only. Returns:
    - total_attacks_24h: Total blocked attacks in last 24 hours
    - by_type: Count by attack type (RATE_LIMIT_EXCEEDED, JWT_INVALID, etc.)
    - by_layer: Count by protection layer (RATE_LIMITER, JWT_GUARD, etc.)
    - top_attacker_ips: Top 5 attacker IP addresses with counts
    """
    require_admin(current_user)

    # Try to get from AttackLog table, fall back to empty stats if table doesn't exist
    try:
        # Calculate 24 hours ago
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

        # Get all attacks in the last 24 hours
        attacks = await prisma.attacklog.find_many(
            where={"timestamp": {"gte": cutoff}},
        )

        total = len(attacks)

        # Count by type
        by_type: dict[str, int] = {}
        for attack in attacks:
            event_type = attack.eventType
            by_type[event_type] = by_type.get(event_type, 0) + 1

        # Count by layer
        by_layer: dict[str, int] = {}
        for attack in attacks:
            layer = attack.protectionLayer or "UNKNOWN"
            by_layer[layer] = by_layer.get(layer, 0) + 1

        # Top attacker IPs
        ip_counts: dict[str, int] = {}
        for attack in attacks:
            ip = attack.attackerIp or "unknown"
            ip_counts[ip] = ip_counts.get(ip, 0) + 1

        # Sort and get top 5
        sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_attacker_ips = [{"ip": ip, "count": count} for ip, count in sorted_ips]

        return AttackSummary(
            total_attacks_24h=total,
            by_type=by_type,
            by_layer=by_layer,
            top_attacker_ips=top_attacker_ips,
        )
    except AttributeError:
        # AttackLog table doesn't exist in Prisma client
        # Return empty stats - table needs to be migrated
        return AttackSummary(
            total_attacks_24h=0,
            by_type={},
            by_layer={},
            top_attacker_ips=[],
        )
