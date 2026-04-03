"""
ScholarClaw — Database Seed Script
Reads seed_data.json and upserts all scholarship schemes.

Usage:  python -m prisma.seed
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend root to path so we can import db
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db import prisma, connect_db, disconnect_db


SEED_FILE = Path(__file__).resolve().parent.parent / "schemes" / "seed_data.json"


async def seed() -> None:
    """Read seed_data.json and upsert every scheme."""
    await connect_db()

    if not SEED_FILE.exists():
        print(f"[ERROR] Seed file not found: {SEED_FILE}")
        return

    with open(SEED_FILE, "r", encoding="utf-8") as f:
        schemes: list[dict] = json.load(f)

    print(f"[SEED] Seeding {len(schemes)} scholarship schemes...")

    for scheme in schemes:
        deadline = None
        if scheme.get("deadline"):
            deadline = datetime.fromisoformat(scheme["deadline"])

        await prisma.scholarshipscheme.upsert(
            where={"id": scheme["id"]},
            data={
                "create": {
                    "id": scheme["id"],
                    "name": scheme["name"],
                    "provider": scheme["provider"],
                    "description": scheme["description"],
                    "amount": scheme["amount"],
                    "deadline": deadline,
                    "eligibilityCriteria": scheme["eligibility_criteria"],
                    "requiredDocuments": scheme["required_documents"],
                    "applicationUrl": scheme.get("application_url", ""),
                },
                "update": {
                    "name": scheme["name"],
                    "provider": scheme["provider"],
                    "description": scheme["description"],
                    "amount": scheme["amount"],
                    "deadline": deadline,
                    "eligibilityCriteria": scheme["eligibility_criteria"],
                    "requiredDocuments": scheme["required_documents"],
                    "applicationUrl": scheme.get("application_url", ""),
                },
            },
        )
        print(f"  [OK] {scheme['name']}")

    await disconnect_db()
    print("[DONE] Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
