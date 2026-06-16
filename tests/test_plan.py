"""Tests for the content plan management module."""

import json
import pytest
from unittest.mock import patch
from src.data.plan import load_plan, save_plan, get_pending_dinosaur, mark_complete, init_plan


class TestLoadPlan:
    """Tests for load_plan()."""

    def test_loads_valid_plan(self, tmp_plan):
        with patch("src.data.plan.PLAN_FILE", tmp_plan):
            plan = load_plan()
            assert "dinosaurs" in plan
            assert isinstance(plan["dinosaurs"], list)

    def test_plan_entries_have_required_fields(self, tmp_plan):
        with patch("src.data.plan.PLAN_FILE", tmp_plan):
            plan = load_plan()
            for dino in plan["dinosaurs"]:
                assert "id" in dino
                assert "status" in dino
                assert dino["status"] in ("pending", "complete")


class TestGetPendingDinosaur:
    """Tests for get_pending_dinosaur()."""

    def test_returns_first_pending(self, tmp_plan):
        with patch("src.data.plan.PLAN_FILE", tmp_plan):
            pending = get_pending_dinosaur()
            assert pending is not None
            assert pending["id"] == "trex"
            assert pending["status"] == "pending"

    def test_returns_none_when_all_complete(self, tmp_plan):
        # Overwrite plan so all are complete
        plan = json.loads(tmp_plan.read_text())
        for dino in plan["dinosaurs"]:
            dino["status"] = "complete"
            dino["published_date"] = "2026-06-15T09:30:00Z"
        tmp_plan.write_text(json.dumps(plan, indent=2))

        with patch("src.data.plan.PLAN_FILE", tmp_plan):
            assert get_pending_dinosaur() is None


class TestMarkComplete:
    """Tests for mark_complete()."""

    def test_marks_dinosaur_complete(self, tmp_plan):
        with patch("src.data.plan.PLAN_FILE", tmp_plan):
            mark_complete("trex")
            plan = load_plan()
            trex = next(d for d in plan["dinosaurs"] if d["id"] == "trex")
            assert trex["status"] == "complete"
            assert trex["published_date"] is not None

    def test_sets_custom_date(self, tmp_plan):
        with patch("src.data.plan.PLAN_FILE", tmp_plan):
            mark_complete("trex", published_date="2026-06-20T12:00:00Z")
            plan = load_plan()
            trex = next(d for d in plan["dinosaurs"] if d["id"] == "trex")
            assert trex["published_date"] == "2026-06-20T12:00:00Z"

    def test_does_not_affect_other_entries(self, tmp_plan):
        with patch("src.data.plan.PLAN_FILE", tmp_plan):
            mark_complete("trex")
            plan = load_plan()
            stego = next(d for d in plan["dinosaurs"] if d["id"] == "stegosaurus")
            assert stego["status"] == "complete"  # was already complete


class TestInitPlan:
    """Tests for init_plan()."""

    def test_creates_plan_from_ids(self, tmp_plan):
        with patch("src.data.plan.PLAN_FILE", tmp_plan):
            init_plan(["alpha", "beta", "gamma"])
            plan = load_plan()
            assert len(plan["dinosaurs"]) == 3
            assert all(d["status"] == "pending" for d in plan["dinosaurs"])
            ids = [d["id"] for d in plan["dinosaurs"]]
            assert ids == ["alpha", "beta", "gamma"]
