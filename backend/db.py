"""
ScholarClaw — Database Connection
Prisma async client with connect/disconnect lifecycle.
"""

from prisma import Prisma

# Global Prisma client instance
prisma = Prisma()


async def connect_db() -> None:
    """Connect to the database. Call on app startup."""
    await prisma.connect()


async def disconnect_db() -> None:
    """Disconnect from the database. Call on app shutdown."""
    await prisma.disconnect()
