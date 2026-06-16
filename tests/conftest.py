"""Shared pytest fixtures for Dinopedia tests."""

import json
import pytest
from pathlib import Path


@pytest.fixture
def sample_dinosaur():
    """A single dinosaur dict matching the data/dinosaurs.json schema."""
    return {
        "id": "trex",
        "common_name": "Tyrannosaurus rex",
        "scientific_name": "Tyrannosaurus rex",
        "period": "Late Cretaceous",
        "period_years": "68-66 million years ago",
        "diet": "Carnivore",
        "habitat": "North America",
        "length_m": 12.3,
        "weight_kg": 9000,
        "key_facts": [
            "Largest land carnivore of its time",
            "Bite force of 12,800 newtons",
            "Fossils found in Hell Creek Formation (Montana, Wyoming)",
            "Walked on two powerful hind legs",
            "Had relatively small arms but powerful claws",
        ],
    }


@pytest.fixture
def sample_content():
    """A valid generated-content dict that passes validation."""
    return {
        "article": "A" * 5000,  # 5000 chars — within 4000-8000 range
        "social_snippet": "B" * 190,  # 190 chars — within 150-250 range
        "hashtags": ["#dinosaurs", "#paleontology", "#trex", "#cretaceous", "#fossils"],
    }


@pytest.fixture
def tmp_plan(tmp_path):
    """Create a temporary dinopedia_plan.json and return its path."""
    plan = {
        "dinosaurs": [
            {
                "id": "trex",
                "common_name": "Tyrannosaurus rex",
                "status": "pending",
                "scheduled_for": None,
                "published_date": None,
            },
            {
                "id": "stegosaurus",
                "common_name": "Stegosaurus",
                "status": "complete",
                "scheduled_for": "2026-06-15",
                "published_date": "2026-06-15T09:30:00Z",
            },
        ]
    }
    plan_file = tmp_path / "dinopedia_plan.json"
    plan_file.write_text(json.dumps(plan, indent=2))
    return plan_file
