"""
ScholarClaw — ArmorIQ Middleware
FastAPI middleware for prompt injection detection.
"""

import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from armoriq.guard import get_guard
from audit.attack_logger import log_attack

logger = logging.getLogger("armoriq.middleware")


class ArmorIQMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and block prompt injection attacks.

    Scans incoming request bodies for malicious content.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.guard = get_guard()

        # Endpoints to protect (only check these)
        self.protected_endpoints = [
            "/api/profile",
            "/api/orchestrator/run",
        ]

        # Fields to scan in request bodies
        self.scan_fields = [
            "name", "full_name", "course", "institution",
            "action", "data", "input", "text", "content",
            "scheme_code", "state", "district",  # Additional fields
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and check for injection."""

        # Only scan protected endpoints
        if not any(request.url.path.startswith(ep) for ep in self.protected_endpoints):
            return await call_next(request)

        # Only scan POST/PUT requests with JSON
        if request.method not in ["POST", "PUT"]:
            return await call_next(request)

        # Read and check request body
        try:
            body = await request.json()
        except Exception:
            # Not JSON or empty body - skip
            return await call_next(request)

        # Scan relevant fields
        for field in self.scan_fields:
            if field in body and isinstance(body[field], str):
                value = body[field]

                # Check for injection
                is_malicious, score, reason = await self.guard.check_injection(value)

                if is_malicious:
                    logger.warning(
                        "ArmorIQ BLOCKED: field=%s, score=%.2f, reason=%s, ip=%s",
                        field,
                        score,
                        reason,
                        request.client.host if request.client else "unknown",
                    )

                    # Log to attack table
                    await log_attack(
                        event_type="PROMPT_INJECTION",
                        attacker_ip=request.client.host if request.client else "unknown",
                        protection_layer="ARMORIQ",
                        block_reason=reason,
                        attack_payload=f"{field}={value[:100]}...",
                    )

                    # Return 403 Forbidden
                    return Response(
                        status_code=403,
                        content='{"detail":"Prompt injection detected"}',
                        media_type="application/json",
                    )

        # All checks passed - continue
        return await call_next(request)
