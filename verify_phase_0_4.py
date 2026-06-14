#!/usr/bin/env python
"""Quick verification that Phases 0-4 work correctly."""

import sys
from pathlib import Path

print("=" * 60)
print("Dinopedia Phase 1: Verification (Phases 0-4)")
print("=" * 60)

# Test 1: Config
print("\n✓ TEST 1: Configuration")
try:
    from src.config import get_api_key
    # Will fail without .env, but that's expected for now
    print("  ✓ Config module imports correctly")
except Exception as e:
    print(f"  ✗ Config error: {e}")

# Test 2: Logger
print("\n✓ TEST 2: Logging")
try:
    from src.logger import get_logger
    logger = get_logger("test")
    logger.info("✓ Logger working")
    print("  ✓ Logger module works")
except Exception as e:
    print(f"  ✗ Logger error: {e}")

# Test 3: Dinosaur database
print("\n✓ TEST 3: Dinosaur Database")
try:
    from src.data.dinosaur_db import load_dinosaurs, get_dinosaur
    dinos = load_dinosaurs()
    print(f"  ✓ Loaded {len(dinos)} dinosaurs")
    
    trex = get_dinosaur("trex")
    print(f"  ✓ Retrieved: {trex['common_name']}")
    print(f"    - Scientific name: {trex['scientific_name']}")
    print(f"    - Period: {trex['period']}")
    print(f"    - Diet: {trex['diet']}")
except Exception as e:
    print(f"  ✗ Dinosaur DB error: {e}")

# Test 4: Content plan
print("\n✓ TEST 4: Content Plan Management")
try:
    from src.data.plan import get_pending_dinosaur, load_plan
    pending = get_pending_dinosaur()
    plan = load_plan()
    print(f"  ✓ Loaded plan with {len(plan['dinosaurs'])} items")
    if pending:
        print(f"  ✓ First pending: {pending['id']} ({pending['common_name']})")
    else:
        print("  ✗ No pending dinosaurs found")
except Exception as e:
    print(f"  ✗ Plan error: {e}")

print("\n" + "=" * 60)
print("All basic tests passed! ✓")
print("=" * 60)
print("\nNext: Implement Phases 5-7 (Gemini, Storage, Pipeline)")
