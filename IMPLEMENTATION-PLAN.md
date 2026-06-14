# Dinopedia Phase 1: Implementation Plan

**Goal**: Get from zero to one — daily dinosaur content generation running autonomously.

**Timeline**: 6-8 hours of focused work (can be split across days)

**Definition of Done**: All 8 checkpoints passing + daily GitHub Actions run successful

---

## Pre-Implementation Checklist

Before starting, verify you have:
- [ ] Google API key (Gemini 2.5 Flash access)
- [ ] GitHub account with push access to dinopedia repo
- [ ] Python 3.11+ installed locally
- [ ] Text editor or IDE (VS Code recommended)
- [ ] 50+ dinosaur facts compiled or ready to create

---

## Implementation Phases

### Phase 0: Scaffolding (20 min)
**Goal**: Create folder structure and boilerplate files

**Steps**:
1. Create folder structure exactly as in PROMPT-PHASE-1.md
2. Create empty `__init__.py` files in all packages
3. Create `.gitignore` (standard Python patterns + output/)

**Verification Checkpoint**:
```bash
cd dinopedia
find src -name "*.py" | wc -l  # Should show all __init__.py + module files
ls -la                          # Verify .gitignore exists
```

**Success Criteria**: Folder structure matches PROMPT-PHASE-1.md diagram exactly

---

### Phase 1: Configuration (15 min)
**Goal**: Environment setup and secrets management

**Steps**:
1. Create `src/config.py` that:
   - Loads `GOOGLE_API_KEY` from `.env` or environment
   - Provides `get_api_key()` function
   - Fails loudly if key missing
2. Create `.env.example` with placeholder
3. Create `.env` (local, gitignored) with actual key

**Code template** (src/config.py):
```python
import os
from dotenv import load_dotenv

load_dotenv()

def get_api_key():
    """Get Gemini API key from environment."""
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError("GOOGLE_API_KEY not set in .env")
    return key
```

**Verification Checkpoint**:
```bash
python -c "from src.config import get_api_key; print(get_api_key())"
# Should print your API key without errors
```

**Success Criteria**: 
- API key loads successfully
- Error message clear if key missing
- `.env` in `.gitignore`

---

### Phase 2: Logging Setup (10 min)
**Goal**: Simple structured logging for debugging

**Steps**:
1. Create `src/logger.py` with:
   - Basic Python logger setup
   - Timestamp + level + message format
   - Console output (no file logging yet)

**Code template** (src/logger.py):
```python
import logging
import sys

def get_logger(name):
    """Configure logger with consistent format."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger
```

**Verification Checkpoint**:
```bash
python -c "from src.logger import get_logger; log = get_logger('test'); log.info('Test')"
# Should print timestamped log message
```

**Success Criteria**: Logger outputs formatted messages to console

---

### Phase 3: Data Models (30 min)
**Goal**: Define dinosaur and content schemas

**Steps**:

#### 3a. Create `data/dinosaurs.json` (15 min)
1. Populate with 50-75 dinosaurs
2. Each must have: id, common_name, scientific_name, period, period_years, diet, habitat, length_m, weight_kg, key_facts (list of 3-5 strings)
3. Validate JSON syntax

**Template**:
```json
{
  "dinosaurs": [
    {
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
        "Largest land carnivore",
        "Bite force of 12,800 newtons",
        "Fossils found in Hell Creek Formation"
      ]
    }
    // ... add 49 more dinosaurs
  ]
}
```

**Verification Checkpoint**:
```bash
python -c "import json; json.load(open('data/dinosaurs.json')); print('✓ Valid JSON')"
python -c "import json; d=json.load(open('data/dinosaurs.json')); print(f'Dinosaurs: {len(d[\"dinosaurs\"])}')"
# Should print count >= 50
```

**Success Criteria**: 
- Valid JSON
- 50+ dinosaurs
- All required fields present

#### 3b. Create `src/data/dinosaur_db.py` (10 min)
Simple loader for dinosaur facts.

```python
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
```

**Verification Checkpoint**:
```bash
python -c "from src.data.dinosaur_db import load_dinosaurs; print(len(load_dinosaurs()))"
# Should print count >= 50
```

**Success Criteria**: Can load and retrieve dinosaurs without errors

---

### Phase 4: Content Plan Management (30 min)
**Goal**: Track which dinosaurs have been generated

**Steps**:

#### 4a. Initialize `dinopedia_plan.json` (10 min)
Create plan file with all dinosaurs marked "pending":

```json
{
  "dinosaurs": [
    {
      "id": "trex",
      "common_name": "Tyrannosaurus rex",
      "status": "pending",
      "scheduled_for": null,
      "published_date": null
    },
    // ... one entry per dinosaur in data/dinosaurs.json
  ]
}
```

**Verification Checkpoint**:
```bash
python -c "import json; p=json.load(open('dinopedia_plan.json')); print(f'Plan items: {len(p[\"dinosaurs\"])}')"
# Should match dinosaurs.json count
```

#### 4b. Create `src/data/plan.py` (20 min)
Manage plan state.

```python
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
```

**Verification Checkpoint**:
```bash
python -c "from src.data.plan import get_pending_dinosaur; d = get_pending_dinosaur(); print(d['id'] if d else 'None')"
# Should print first dinosaur id (e.g., 'trex')

python -c "from src.data.plan import mark_complete; mark_complete('trex'); from src.data.plan import get_pending_dinosaur; print(get_pending_dinosaur()['id'])"
# Should print second dinosaur (trex now complete)
```

**Success Criteria**: 
- Can get pending dinosaur
- Can mark complete
- Plan persists to disk

---

### Phase 5: Gemini Integration (45 min)
**Goal**: Connect to Gemini API for content generation

**Steps**:

#### 5a. Create `src/generation/prompts.py` (15 min)
Centralized prompt templates.

```python
def get_article_prompt(dinosaur):
    """Generate prompt for dinosaur article."""
    return f"""
    You are an expert paleontologist writing for a general audience (no prior knowledge assumed).
    
    Generate an educational article about {dinosaur['common_name']}.
    
    FACTS PROVIDED:
    - Scientific name: {dinosaur['scientific_name']}
    - Period: {dinosaur['period']} ({dinosaur['period_years']})
    - Diet: {dinosaur['diet']}
    - Habitat: {dinosaur['habitat']}
    - Length: {dinosaur['length_m']}m
    - Weight: {dinosaur['weight_kg']}kg
    - Key facts: {', '.join(dinosaur['key_facts'])}
    
    REQUIREMENTS:
    1. Write a compelling article (800-1200 words)
    2. Start with an engaging hook
    3. Explain what made this dinosaur unique
    4. Use simple analogies for complex concepts
    5. End with "Did you know?" section
    
    Also provide:
    - A 1-sentence summary for social media (180-200 chars)
    - 5-7 hashtags relevant to this dinosaur
    
    Return ONLY valid JSON (no markdown, no code blocks) with this structure:
    {{
      "article": "full article text",
      "short": "social media summary",
      "hashtags": ["#tag1", "#tag2", ...]
    }}
    """

def get_short_prompt(dinosaur):
    """Generate prompt for social media snippet."""
    return f"""
    Create a viral-worthy 1-2 sentence fact about {dinosaur['common_name']}.
    
    Facts: {', '.join(dinosaur['key_facts'])}
    
    Requirements:
    - Exactly 1-2 sentences
    - Under 200 characters
    - Engaging and shareable
    - No hashtags in text
    
    Return ONLY the text (no JSON, no quotes).
    """
```

**Verification Checkpoint**: Just syntax check
```bash
python -c "from src.generation.prompts import get_article_prompt; print('✓ Prompts loaded')"
```

#### 5b. Create `src/generation/gemini_service.py` (20 min)
API wrapper.

```python
import json
import google.genai as genai
from src.config import get_api_key
from src.logger import get_logger

logger = get_logger(__name__)

def init_gemini():
    """Initialize Gemini client."""
    api_key = get_api_key()
    genai.configure(api_key=api_key)
    logger.info("Gemini initialized")

def generate_content(prompt, model="gemini-2.5-flash"):
    """Call Gemini API."""
    logger.info(f"Calling Gemini ({model})...")
    
    client = genai.Client(api_key=get_api_key())
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    
    text = response.text.strip()
    logger.info(f"Response received ({len(text)} chars)")
    return text

def generate_dinosaur_article(dinosaur):
    """Generate article for a dinosaur."""
    from src.generation.prompts import get_article_prompt
    
    prompt = get_article_prompt(dinosaur)
    response_text = generate_content(prompt)
    
    # Parse JSON response
    try:
        content = json.loads(response_text)
        logger.info("✓ Article generated successfully")
        return content
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response: {e}")
        logger.error(f"Response was: {response_text[:200]}")
        raise
```

**Verification Checkpoint** (requires API key):
```bash
python -c "
from src.generation.gemini_service import init_gemini, generate_dinosaur_article
from src.data.dinosaur_db import get_dinosaur
init_gemini()
dino = get_dinosaur('trex')
content = generate_dinosaur_article(dino)
print(f'Article length: {len(content[\"article\"])} chars')
print(f'Short length: {len(content[\"short\"])} chars')
print(f'Hashtags: {len(content[\"hashtags\"])}')
"
# Should print lengths without errors
```

**Success Criteria**: 
- Gemini connects without errors
- Returns valid JSON
- All required fields present
- No API errors

#### 5c. Create `src/generation/content_generator.py` (10 min)
Orchestration layer.

```python
import json
from pathlib import Path
from src.generation.gemini_service import generate_dinosaur_article
from src.data.dinosaur_db import get_dinosaur
from src.logger import get_logger

logger = get_logger(__name__)

def generate_dinosaur_content(dinosaur_id):
    """Generate and validate content for a dinosaur."""
    logger.info(f"Generating content for {dinosaur_id}...")
    
    # Get dinosaur facts
    dinosaur = get_dinosaur(dinosaur_id)
    
    # Generate via Gemini
    content = generate_dinosaur_article(dinosaur)
    
    # Validate
    assert "article" in content, "Missing 'article' field"
    assert "short" in content, "Missing 'short' field"
    assert "hashtags" in content, "Missing 'hashtags' field"
    assert len(content["short"]) <= 200, f"Short too long: {len(content['short'])}"
    assert len(content["hashtags"]) >= 5, f"Too few hashtags: {len(content['hashtags'])}"
    
    logger.info("✓ Content validated")
    return content
```

**Verification Checkpoint**:
```bash
python -c "from src.generation.content_generator import generate_dinosaur_content; content = generate_dinosaur_content('trex'); print('✓ Content generated')"
```

---

### Phase 6: Storage & Output (30 min)
**Goal**: Save generated content to disk

**Steps**:

#### 6a. Create `src/utils/file_io.py` (10 min)
```python
import json
from pathlib import Path
from datetime import datetime

def save_json(filename, data):
    """Save data as JSON."""
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    return str(path)

def load_json(filename):
    """Load data from JSON."""
    with open(filename) as f:
        return json.load(f)

def save_markdown(filename, title, content):
    """Save content as markdown."""
    md = f"# {title}\n\n{content}"
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(md)
    return str(path)
```

#### 6b. Create `src/data/repository.py` (20 min)
Save generated content.

```python
import json
from datetime import datetime
from pathlib import Path
from src.logger import get_logger

logger = get_logger(__name__)
OUTPUT_DIR = Path("output")

def save_article(dinosaur_id, content):
    """Save generated article to disk."""
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # JSON version
    json_data = {
        "id": f"{dinosaur_id}_{timestamp}",
        "dinosaur_id": dinosaur_id,
        "date_generated": datetime.now().isoformat(),
        "article": content["article"],
        "short": content["short"],
        "metadata": {
            "hashtags": content["hashtags"],
            "keywords": content.get("keywords", [])
        }
    }
    
    json_path = OUTPUT_DIR / "articles" / f"{dinosaur_id}_{timestamp}.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    logger.info(f"✓ Saved JSON: {json_path}")
    
    # Markdown version
    md_content = f"""# {json_data['dinosaur_id'].upper()}

{content['article']}

## Social Media Summary

{content['short']}

## Metadata

**Hashtags**: {' '.join(content['hashtags'])}

**Generated**: {datetime.now().isoformat()}
"""
    
    md_path = OUTPUT_DIR / "articles" / f"{dinosaur_id}_{timestamp}.md"
    with open(md_path, 'w') as f:
        f.write(md_content)
    
    logger.info(f"✓ Saved Markdown: {md_path}")
    
    return {
        "json": str(json_path),
        "markdown": str(md_path)
    }
```

**Verification Checkpoint**:
```bash
python -c "
from src.generation.content_generator import generate_dinosaur_content
from src.data.repository import save_article

content = generate_dinosaur_content('trex')
paths = save_article('trex', content)
print(f'Saved: {paths}')
"
# Should create files in output/articles/
ls output/articles/  # Should show trex_YYYYMMDD.json and .md
```

---

### Phase 7: Main Pipeline (30 min)
**Goal**: Tie everything together in entry point

**Steps**:

Create `src/main.py`:

```python
import sys
import traceback
from datetime import datetime
from src.config import get_api_key
from src.logger import get_logger
from src.generation.gemini_service import init_gemini
from src.generation.content_generator import generate_dinosaur_content
from src.data.repository import save_article
from src.data.plan import get_pending_dinosaur, mark_complete

logger = get_logger(__name__)

def main():
    """Main pipeline: generate → save → update plan."""
    logger.info("🦕 Dinopedia Generation Started")
    
    try:
        # Initialize Gemini
        init_gemini()
        
        # Get next dinosaur
        pending = get_pending_dinosaur()
        if not pending:
            logger.info("✅ All dinosaurs completed!")
            return 0
        
        dinosaur_id = pending["id"]
        logger.info(f"Processing: {dinosaur_id}")
        
        # Generate content
        content = generate_dinosaur_content(dinosaur_id)
        
        # Save to disk
        paths = save_article(dinosaur_id, content)
        logger.info(f"✓ Saved to {paths['json']}")
        
        # Update plan
        mark_complete(dinosaur_id, datetime.now().isoformat())
        logger.info(f"✓ Updated plan: {dinosaur_id} → complete")
        
        logger.info("🎉 Generation complete!")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Verification Checkpoint**:
```bash
python src/main.py
# Should output:
# 🦕 Dinopedia Generation Started
# Processing: trex
# ✓ Article generated ...
# ✓ Saved to output/articles/trex_YYYYMMDD.json
# ✓ Updated plan: trex → complete
# 🎉 Generation complete!

cat dinopedia_plan.json | grep -A2 '"trex"'
# Should show "status": "complete"
```

**Success Criteria**: 
- Script runs without errors
- Files saved to output/
- Plan updated in dinopedia_plan.json

---

### Phase 8: Testing (20 min)
**Goal**: Add basic test suite

**Steps**:

Create `tests/test_generation.py`:

```python
import pytest
from src.data.dinosaur_db import load_dinosaurs, get_dinosaur
from src.generation.content_generator import generate_dinosaur_content
from src.data.plan import get_pending_dinosaur, mark_complete

def test_load_dinosaurs():
    """Test dinosaur database loads."""
    dinosaurs = load_dinosaurs()
    assert len(dinosaurs) >= 50
    assert dinosaurs[0]["id"]
    assert dinosaurs[0]["common_name"]

def test_get_dinosaur():
    """Test retrieve single dinosaur."""
    dino = get_dinosaur("trex")
    assert dino["common_name"] == "Tyrannosaurus rex"

def test_pending_dinosaur():
    """Test content plan tracks pending."""
    pending = get_pending_dinosaur()
    assert pending is not None
    assert pending["status"] == "pending"

def test_mark_complete():
    """Test marking dinosaur complete."""
    pending_before = get_pending_dinosaur()
    dino_id = pending_before["id"]
    
    mark_complete(dino_id)
    
    pending_after = get_pending_dinosaur()
    assert pending_after["id"] != dino_id  # Changed to next
```

Create `tests/test_data.py`:

```python
import pytest
from src.data.plan import load_plan, save_plan

def test_plan_structure():
    """Test plan has correct structure."""
    plan = load_plan()
    assert "dinosaurs" in plan
    assert len(plan["dinosaurs"]) > 0
    
    for dino in plan["dinosaurs"]:
        assert "id" in dino
        assert "status" in dino
        assert dino["status"] in ["pending", "complete"]
```

**Verification Checkpoint**:
```bash
pip install pytest
pytest tests/ -v
# Should show tests passing
```

**Success Criteria**: All tests pass

---

### Phase 9: GitHub Actions (30 min)
**Goal**: Automate daily runs

**Steps**:

Create `.github/workflows/daily-generation.yml`:

```yaml
name: Daily Dinosaur Generation

on:
  schedule:
    - cron: '0 7 * * *'  # 7 AM UTC daily
  workflow_dispatch:

jobs:
  generate:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - name: ⬇️ Checkout
        uses: actions/checkout@v4

      - name: 🐍 Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: 📦 Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: 🚀 Generate dinosaur content
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: python src/main.py

      - name: 💾 Commit & push
        if: success()
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add dinopedia_plan.json output/
          git commit -m "Daily dinosaur: $(date +%Y-%m-%d)" || echo "No changes"
          git push

      - name: ⚠️ Notify on failure
        if: failure()
        run: |
          echo "❌ Pipeline failed"
          exit 1
```

**Verification Checkpoint**:
1. Push to GitHub
2. Go to Actions tab
3. Manually trigger workflow
4. Should complete successfully
5. Check that:
   - dinopedia_plan.json updated
   - output/articles/ has new files
   - Commit appears in history

**Success Criteria**: Workflow runs and commits results

---

### Phase 10: Final Validation (15 min)
**Goal**: Verify all 8 checkpoints from PROMPT-PHASE-1.md

**Checklist**:

```bash
# 1. Setup ✓
pip list | grep google-genai

# 2. Config ✓
python -c "from src.config import get_api_key; print(get_api_key())"

# 3. Data ✓
python -c "import json; d=json.load(open('data/dinosaurs.json')); print(f'Dinosaurs: {len(d[\"dinosaurs\"])}')"

# 4. Plan ✓
cat dinopedia_plan.json | head -20

# 5. Generation ✓
python src/main.py

# 6. Storage ✓
ls -la output/articles/

# 7. Plan Update ✓
cat dinopedia_plan.json | grep -c '"complete"'

# 8. GitHub Actions ✓
# Go to Actions tab and verify workflow ran
```

---

## Summary Timeline

| Phase | Task | Time | Cumulative |
|-------|------|------|-----------|
| 0 | Scaffolding | 20 min | 20 min |
| 1 | Configuration | 15 min | 35 min |
| 2 | Logging | 10 min | 45 min |
| 3 | Data Models | 30 min | 75 min |
| 4 | Plan Management | 30 min | 105 min |
| 5 | Gemini Integration | 45 min | 150 min |
| 6 | Storage & Output | 30 min | 180 min |
| 7 | Main Pipeline | 30 min | 210 min |
| 8 | Testing | 20 min | 230 min |
| 9 | GitHub Actions | 30 min | 260 min |
| 10 | Final Validation | 15 min | 275 min |

**Total: ~4.5 hours of focused, step-by-step implementation**

---

## Blockers & Solutions

| Blocker | Solution |
|---------|----------|
| Gemini API errors | Check API key in .env, verify account quota |
| JSON parsing fails | Log response text, check Gemini prompt format |
| Plan not updating | Verify save_plan() writes to correct path |
| GitHub Actions fails | Check secrets in repo settings |
| File permissions | Ensure output/ writable on GitHub runner |

---

## Success Criteria (Phase 1 Complete)

**All of these must be true**:

- [ ] ✅ Checkpoint 1: Setup (Python env works)
- [ ] ✅ Checkpoint 2: Config (API key loads)
- [ ] ✅ Checkpoint 3: Data (50+ dinosaurs)
- [ ] ✅ Checkpoint 4: Plan (JSON created)
- [ ] ✅ Checkpoint 5: Generation (Gemini works)
- [ ] ✅ Checkpoint 6: Storage (Files saved)
- [ ] ✅ Checkpoint 7: Plan Update (Status marked)
- [ ] ✅ Checkpoint 8: GitHub Actions (Automated runs)

**Definition of Done**: Run `python src/main.py` successfully 3 times in a row, then GitHub Actions runs it daily without human intervention.

---

## Next: Implementation

Ready to start? Follow each phase in order. Each has clear verification checkpoints — don't move forward if a checkpoint fails.

**Key principle**: Test after each phase. Don't assume it works until you verify it.
