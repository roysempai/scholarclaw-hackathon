"""
ScholarClaw — Custom Exceptions & FastAPI Exception Handlers
"""

import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger("exceptions")


# ── Base Exception ────────────────────────────────────────────
class ScholarClawException(Exception):
    """Base exception for all ScholarClaw errors."""

    status_code: int = 500
    detail: str = "An unexpected error occurred"

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)


# ── Auth Exceptions ──────────────────────────────────────────
class AuthenticationError(ScholarClawException):
    status_code = 401
    detail = "Not authenticated"


class AuthorizationError(ScholarClawException):
    status_code = 403
    detail = "Not authorized to access this resource"


# ── Validation ───────────────────────────────────────────────
class ValidationError(ScholarClawException):
    status_code = 422
    detail = "Validation error"


# ── Policy ───────────────────────────────────────────────────
class PolicyBlockedError(ScholarClawException):
    """Raised when a request is blocked by the policy gate."""

    status_code = 403
    detail = "Request blocked by policy"

    def __init__(self, detail: str | None = None, block_reason: str = ""):
        super().__init__(detail)
        self.block_reason = block_reason


# ── Agent ────────────────────────────────────────────────────
class AgentError(ScholarClawException):
    status_code = 500
    detail = "AI agent encountered an error"


# ── Exception Handler Registration ──────────────────────────
def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI app."""

    @app.exception_handler(ScholarClawException)
    async def scholarclaw_exception_handler(
        request: Request, exc: ScholarClawException
    ) -> JSONResponse:
        body: dict = {"detail": exc.detail}
        if isinstance(exc, PolicyBlockedError) and exc.block_reason:
            body["block_reason"] = exc.block_reason
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Don't catch HTTPException - let FastAPI handle it
        if isinstance(exc, HTTPException):
            raise exc

        # Log the actual error for debugging
        logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)

        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"},
        )
