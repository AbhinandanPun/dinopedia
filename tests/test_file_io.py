"""Tests for the file I/O utility module."""

import json
import pytest
from pathlib import Path
from src.utils.file_io import ensure_directory, save_json, read_json, save_text, read_text


class TestEnsureDirectory:
    """Tests for ensure_directory()."""

    def test_creates_directory(self, tmp_path):
        target = tmp_path / "a" / "b" / "c"
        assert not target.exists()
        result = ensure_directory(target)
        assert target.exists()
        assert target.is_dir()
        assert result == target

    def test_idempotent(self, tmp_path):
        target = tmp_path / "existing"
        target.mkdir()
        ensure_directory(target)  # should not raise
        assert target.is_dir()


class TestJsonRoundTrip:
    """Tests for save_json() and read_json()."""

    def test_basic_dict(self, tmp_path):
        filepath = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        save_json(data, filepath)
        loaded = read_json(filepath)
        assert loaded == data

    def test_nested_structure(self, tmp_path):
        filepath = tmp_path / "nested.json"
        data = {
            "dinosaurs": [
                {"id": "trex", "facts": ["big", "scary"]},
                {"id": "stego", "facts": ["plates", "tail spikes"]},
            ]
        }
        save_json(data, filepath)
        loaded = read_json(filepath)
        assert loaded == data

    def test_creates_parent_directories(self, tmp_path):
        filepath = tmp_path / "deep" / "nested" / "file.json"
        save_json({"ok": True}, filepath)
        assert filepath.exists()
        assert read_json(filepath) == {"ok": True}


class TestTextRoundTrip:
    """Tests for save_text() and read_text()."""

    def test_basic_text(self, tmp_path):
        filepath = tmp_path / "test.txt"
        text = "Hello, Dinopedia!"
        save_text(text, filepath)
        loaded = read_text(filepath)
        assert loaded == text

    def test_multiline_text(self, tmp_path):
        filepath = tmp_path / "multi.md"
        text = "# Title\n\nParagraph one.\n\nParagraph two.\n"
        save_text(text, filepath)
        loaded = read_text(filepath)
        assert loaded == text

    def test_creates_parent_directories(self, tmp_path):
        filepath = tmp_path / "a" / "b" / "output.txt"
        save_text("content", filepath)
        assert filepath.exists()
        assert read_text(filepath) == "content"
