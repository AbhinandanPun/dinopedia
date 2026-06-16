#!/usr/bin/env python
"""Phase 10: Final validation — verifies all 8 success criteria for Phase 1 MVP."""

import sys
import subprocess
from pathlib import Path

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        msg = f"  ✗ {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)


print("=" * 70)
print("Dinopedia Phase 1 MVP — Final Validation (Phase 10)")
print("=" * 70)

# ---------- Checkpoint 1: Setup ----------
print("\n[1/8] Setup: Python env & dependencies")
try:
    import google.genai
    check("google-genai installed", True)
except ImportError:
    check("google-genai installed", False, "pip install google-genai")

try:
    import dotenv
    check("python-dotenv installed", True)
except ImportError:
    check("python-dotenv installed", False, "pip install python-dotenv")

try:
    import pytest
    check("pytest installed", True)
except ImportError:
    check("pytest installed", False, "pip install pytest")

# ---------- Checkpoint 2: Config ----------
print("\n[2/8] Config: API key loads from .env")
try:
    from src.config import get_api_key
    key = get_api_key()
    check("API key loads", key and len(key) > 10, f"{len(key)} chars")
except Exception as e:
    check("API key loads", False, str(e))

# ---------- Checkpoint 3: Data ----------
print("\n[3/8] Data: Dinosaurs database")
try:
    from src.data.dinosaur_db import load_dinosaurs
    dinos = load_dinosaurs()
    check("data/dinosaurs.json loads", True)
    check(f"Dinosaur count: {len(dinos)}", len(dinos) >= 20,
          f"Expected 20+, got {len(dinos)}")
except Exception as e:
    check("data/dinosaurs.json loads", False, str(e))

# ---------- Checkpoint 4: Plan ----------
print("\n[4/8] Plan: dinopedia_plan.json")
plan_path = Path("dinopedia_plan.json")
check("dinopedia_plan.json exists", plan_path.exists())
if plan_path.exists():
    try:
        from src.data.plan import load_plan
        plan = load_plan()
        check(f"Plan has {len(plan['dinosaurs'])} dinosaurs",
              len(plan["dinosaurs"]) >= 20)
    except Exception as e:
        check("Plan loads", False, str(e))

# ---------- Checkpoint 5: Generation modules ----------
print("\n[5/8] Generation: All modules importable")
try:
    from src.generation.gemini_service import init_gemini, generate_content
    check("gemini_service importable", True)
except Exception as e:
    check("gemini_service importable", False, str(e))

try:
    from src.generation.content_generator import generate_dinosaur_content
    check("content_generator importable", True)
except Exception as e:
    check("content_generator importable", False, str(e))

try:
    from src.generation.prompts import get_article_prompt, get_short_prompt
    check("prompts importable", True)
except Exception as e:
    check("prompts importable", False, str(e))

# ---------- Checkpoint 6: Storage ----------
print("\n[6/8] Storage: output/ directories")
check("output/ exists", Path("output").exists())
check("output/articles/ exists", Path("output/articles").exists())
check("output/metadata/ exists", Path("output/metadata").exists())

# ---------- Checkpoint 7: Tests pass ----------
print("\n[7/8] Tests: pytest")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
        capture_output=True, text=True, timeout=60
    )
    passed = result.returncode == 0
    # Count results from output
    for line in result.stdout.splitlines():
        if "passed" in line or "failed" in line:
            print(f"       {line.strip()}")
    check("All unit tests pass", passed,
          "" if passed else "See output above")
except Exception as e:
    check("pytest runs", False, str(e))

# ---------- Checkpoint 8: GitHub Actions ----------
print("\n[8/8] GitHub Actions: Workflow file")
workflow = Path(".github/workflows/daily-generation.yml")
check("daily-generation.yml exists", workflow.exists())
if workflow.exists():
    text = workflow.read_text(encoding="utf-8")
    check("Has cron schedule", "cron:" in text)
    check("Has workflow_dispatch", "workflow_dispatch" in text)
    check("Uses GOOGLE_API_KEY secret", "GOOGLE_API_KEY" in text)
    check("Runs src.main", "src.main" in text)

# ---------- Summary ----------
total = PASS + FAIL
print("\n" + "=" * 70)
if FAIL == 0:
    print(f"🎉 ALL {PASS} CHECKS PASSED — Phase 1 MVP is complete!")
else:
    print(f"⚠️  {PASS}/{total} checks passed, {FAIL} failed")
print("=" * 70)

sys.exit(1 if FAIL > 0 else 0)
