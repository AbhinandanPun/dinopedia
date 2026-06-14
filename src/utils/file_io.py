"""Utility functions for file I/O operations."""

import json
from pathlib import Path
from src.logger import get_logger

logger = get_logger(__name__)

def ensure_directory(path):
    """Ensure directory exists, create if needed."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_json(data, filepath):
    """Save data as JSON file."""
    filepath = Path(filepath)
    ensure_directory(filepath.parent)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved JSON: {filepath}")

def save_text(text, filepath):
    """Save text to file."""
    filepath = Path(filepath)
    ensure_directory(filepath.parent)
    with open(filepath, 'w') as f:
        f.write(text)
    logger.info(f"Saved text: {filepath}")

def read_json(filepath):
    """Read JSON file."""
    with open(filepath) as f:
        return json.load(f)

def read_text(filepath):
    """Read text file."""
    with open(filepath) as f:
        return f.read()
