"""Tests for the dinosaur database module."""

import pytest
from src.data.dinosaur_db import load_dinosaurs, get_dinosaur


class TestLoadDinosaurs:
    """Tests for load_dinosaurs()."""

    def test_returns_list(self):
        dinosaurs = load_dinosaurs()
        assert isinstance(dinosaurs, list)

    def test_has_entries(self):
        dinosaurs = load_dinosaurs()
        assert len(dinosaurs) >= 20, f"Expected 20+ dinosaurs, got {len(dinosaurs)}"

    def test_entry_has_required_fields(self):
        dinosaurs = load_dinosaurs()
        required = [
            "id", "common_name", "scientific_name",
            "period", "period_years", "diet", "habitat",
            "length_m", "weight_kg", "key_facts",
        ]
        for dino in dinosaurs:
            for field in required:
                assert field in dino, f"Dinosaur {dino.get('id', '?')} missing '{field}'"


class TestGetDinosaur:
    """Tests for get_dinosaur()."""

    def test_known_dinosaur(self):
        dino = get_dinosaur("trex")
        assert dino["common_name"] == "Tyrannosaurus rex"
        assert dino["diet"] == "Carnivore"

    def test_has_key_facts(self):
        dino = get_dinosaur("trex")
        assert isinstance(dino["key_facts"], list)
        assert len(dino["key_facts"]) >= 3

    def test_numeric_fields(self):
        dino = get_dinosaur("trex")
        assert isinstance(dino["length_m"], (int, float))
        assert isinstance(dino["weight_kg"], (int, float))
        assert dino["length_m"] > 0
        assert dino["weight_kg"] > 0

    def test_nonexistent_raises(self):
        with pytest.raises(ValueError, match="not found"):
            get_dinosaur("nonexistent_dino")
