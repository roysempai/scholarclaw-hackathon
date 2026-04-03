"""
ScholarClaw — FastAPI Application Entry Point
Main application with lifespan for database and scheduler.
"""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import settings
from db import connect_db, disconnect_db
from exceptions import register_exception_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("main")

# APScheduler instance
scheduler = AsyncIOScheduler()


# ── Lifespan Context Manager ─────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    Startup:
    - Connect to database
    - Start APScheduler with reminder job

    Shutdown:
    - Stop scheduler
    - Disconnect from database
    """
    logger.info("Starting ScholarClaw backend...")

    # Connect to database
    await connect_db()
    logger.info("Database connected")

    # Register reminder job (runs every 24 hours)
    from agents.reminder_agent import run_reminder_job

    scheduler.add_job(
        run_reminder_job,
        trigger=IntervalTrigger(hours=24),
        id="reminder_job",
        name="Daily Reminder Check",
        replace_existing=True,
    )

    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started with reminder job (24h interval)")

    yield  # Application runs here

    # Shutdown
    logger.info("Shutting down ScholarClaw backend...")

    # Stop scheduler
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")

    # Disconnect from database
    await disconnect_db()
    logger.info("Database disconnected")


# ── FastAPI Application ──────────────────────────────────────────


app = FastAPI(
    title="ScholarClaw",
    description="AI-powered scholarship matching and application platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Register exception handlers
register_exception_handlers(app)

# CORS middleware
import os
_frontend_url = os.environ.get("FRONTEND_URL", settings.FRONTEND_URL)
_allowed_origins = [
    _frontend_url,
    "https://frontend-gold-omega-16.vercel.app",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
]
# Remove duplicates and empty strings
_allowed_origins = list(set(o for o in _allowed_origins if o))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ArmorIQ middleware (Prompt Injection Detection)
from armoriq.middleware import ArmorIQMiddleware
app.add_middleware(ArmorIQMiddleware)


# ── Register Routers ─────────────────────────────────────────────


# Auth router
from auth.router import router as auth_router
app.include_router(auth_router)

# Profile router
from profile.router import router as profile_router
app.include_router(profile_router)

# Schemes router
from schemes.router import router as schemes_router
app.include_router(schemes_router)

# Audit router
from audit.router import router as audit_router
app.include_router(audit_router)

# Orchestrator router
from orchestrator.router import router as orchestrator_router
app.include_router(orchestrator_router)


# ── Health Check ─────────────────────────────────────────────────


@app.get("/health")
async def health_check():
    """Application health check endpoint."""
    return {
        "status": "healthy",
        "service": "scholarclaw-backend",
        "scheduler_running": scheduler.running,
    }


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "ScholarClaw API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ── Run Server ───────────────────────────────────────────────────


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
