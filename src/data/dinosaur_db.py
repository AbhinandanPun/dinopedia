import json
from pathlib import Path

def load_dinosaurs():
    """Load all dinosaurs from data/dinosaurs.json."""
    path = Path("data/dinosaurs.json")
    with open(path) as f:
        data = json.load(f)
    return data["dinosaurs"]

def get_dinosaur(dinosaur_id):
    """Get single dinosaur by id."""
    dinosaurs = load_dinosaurs()
    for d in dinosaurs:
        if d["id"] == dinosaur_id:
            return d
    raise ValueError(f"Dinosaur not found: {dinosaur_id}")
