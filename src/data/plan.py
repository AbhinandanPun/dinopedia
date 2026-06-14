import json
from datetime import datetime
from pathlib import Path

PLAN_FILE = Path("dinopedia_plan.json")

def load_plan():
    """Load current content plan."""
    with open(PLAN_FILE) as f:
        return json.load(f)

def save_plan(plan):
    """Save plan to disk."""
    with open(PLAN_FILE, 'w') as f:
        json.dump(plan, f, indent=2)

def get_pending_dinosaur():
    """Return first dinosaur with status='pending', or None."""
    plan = load_plan()
    for dino in plan["dinosaurs"]:
        if dino["status"] == "pending":
            return dino
    return None

def mark_complete(dinosaur_id, published_date=None):
    """Mark dinosaur as 'complete'."""
    plan = load_plan()
    for dino in plan["dinosaurs"]:
        if dino["id"] == dinosaur_id:
            dino["status"] = "complete"
            if published_date:
                dino["published_date"] = published_date
            else:
                dino["published_date"] = datetime.now().isoformat()
            break
    save_plan(plan)

def init_plan(dinosaur_ids):
    """Initialize plan with dinosaurs (call once at setup)."""
    plan = {
        "dinosaurs": [
            {
                "id": did,
                "status": "pending",
                "scheduled_for": None,
                "published_date": None
            }
            for did in dinosaur_ids
        ]
    }
    save_plan(plan)
