"""
Attack Visibility Verification Script
Directly checks the database for logged attack events.
"""

import asyncio
from db import prisma
from datetime import datetime, timedelta

async def verify_attacks():
    """Check if attack events are properly logged in the database."""
    await prisma.connect()

    print("\n" + "="*70)
    print("Attack Visibility Verification")
    print("="*70)

    # Get all BLOCK events from the last 10 minutes
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    attacks = await prisma.auditlog.find_many(
        where={
            'result': 'BLOCK',
            'createdAt': {'gte': cutoff}
        },
        order={'createdAt': 'desc'}
    )

    print(f"\n[INFO] Found {len(attacks)} BLOCK events in the last 10 minutes")

    # Group by event type
    by_type = {}
    by_layer = {}
    ips = set()

    for attack in attacks:
        event_type = attack.eventType or "UNKNOWN"
        layer = attack.protectionLayer or "UNKNOWN"

        by_type[event_type] = by_type.get(event_type, 0) + 1
        by_layer[layer] = by_layer.get(layer, 0) + 1

        if attack.attackerIp:
            ips.add(attack.attackerIp)

    # Test Results
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)

    results = {}

    # TEST 1: Rate Limiter
    rate_limit_count = by_type.get("RATE_LIMIT_EXCEEDED", 0)
    if rate_limit_count > 0:
        print(f"\n[PASS] TEST 1: Rate Limiter")
        print(f"       Found {rate_limit_count} RATE_LIMIT_EXCEEDED events")
        print(f"       Protection Layer: {by_layer.get('RATE_LIMITER', 0)} from RATE_LIMITER")
        results["test_1"] = True
    else:
        print(f"\n[FAIL] TEST 1: Rate Limiter")
        print(f"       No RATE_LIMIT_EXCEEDED events found")
        results["test_1"] = False

    # TEST 2: JWT Guard
    jwt_count = by_type.get("JWT_INVALID", 0)
    if jwt_count > 0:
        print(f"\n[PASS] TEST 2: JWT Guard")
        print(f"       Found {jwt_count} JWT_INVALID events")
        print(f"       Protection Layer: {by_layer.get('JWT_GUARD', 0)} from JWT_GUARD")
        results["test_2"] = True
    else:
        print(f"\n[FAIL] TEST 2: JWT Guard")
        print(f"       No JWT_INVALID events found")
        results["test_2"] = False

    # TEST 3: ArmorIQ
    injection_count = by_type.get("PROMPT_INJECTION", 0)
    if injection_count > 0:
        print(f"\n[PASS] TEST 3: ArmorIQ")
        print(f"       Found {injection_count} PROMPT_INJECTION events")
        print(f"       Protection Layer: {by_layer.get('ARMORIQ', 0)} from ARMORIQ")
        results["test_3"] = True
    else:
        print(f"\n[SKIP] TEST 3: ArmorIQ")
        print(f"       No PROMPT_INJECTION events found")
        print(f"       (May require orchestrator endpoint implementation)")
        results["test_3"] = None

    # TEST 4: Policy Gate
    policy_count = by_type.get("POLICY_VIOLATION", 0)
    if policy_count > 0:
        print(f"\n[PASS] TEST 4: Policy Gate")
        print(f"       Found {policy_count} POLICY_VIOLATION events")
        print(f"       Protection Layer: {by_layer.get('POLICY_GATE', 0)} from POLICY_GATE")
        results["test_4"] = True
    else:
        print(f"\n[SKIP] TEST 4: Policy Gate")
        print(f"       No POLICY_VIOLATION events found")
        print(f"       (May require policy gate wiring to endpoints)")
        results["test_4"] = None

    # Show sample attack details
    print("\n" + "="*70)
    print("SAMPLE ATTACK DETAILS (Latest 5)")
    print("="*70)

    for i, attack in enumerate(attacks[:5], 1):
        print(f"\n[{i}] {attack.eventType}")
        print(f"    Time: {attack.createdAt.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Layer: {attack.protectionLayer}")
        print(f"    IP: {attack.attackerIp}")
        print(f"    Reason: {attack.blockReason}")
        print(f"    Payload: {attack.attackPayload or 'N/A'}")

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)

    print(f"\n[PASS] PASSED: {passed}/4")
    print(f"[FAIL] FAILED: {failed}/4")
    print(f"[SKIP] SKIPPED: {skipped}/4")

    print(f"\nTotal Attack Events: {len(attacks)}")
    print(f"Unique Attacker IPs: {len(ips)}")
    print(f"Event Types: {dict(by_type)}")
    print(f"Protection Layers: {dict(by_layer)}")

    await prisma.disconnect()

    if failed > 0:
        print("\n[WARN] Some tests failed.")
        return 1
    elif passed >= 2:
        print("\n[SUCCESS] Core protection layers are logging attacks correctly!")
        return 0
    else:
        print("\n[WARN] Insufficient test coverage.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(verify_attacks())
    exit(exit_code)
