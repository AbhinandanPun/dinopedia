# Spec 05: Multi-Channel Architecture

> **Status**: 📝 Draft  
> **Priority**: 🟡 P2 (Foundation for scale)  
> **Estimated Effort**: 1-2 days  
> **Dependencies**: Specs 01-04 should be designed (not necessarily implemented) first

---

## Problem Statement

The codebase is currently hardcoded for a single "Dinopedia" channel:
- `data/dinosaurs.json` — hardcoded dinosaur data
- `dinopedia_plan.json` — single plan file in root
- `prompts.py` — dinosaur-specific prompt templates
- `config.py` — single API key, no channel awareness
- `youtube_uploader.py` — single set of credentials

To scale to 5-10 channels (Spacepedia, Mythopedia, etc.), the entire pipeline must become **config-driven and channel-agnostic**.

## Proposed Solution

Refactor the pipeline so that **everything channel-specific lives in a config file**, and the shared engine reads that config at runtime.

### Core Principle

```
The pipeline code should NEVER contain the word "dinosaur".
It should only speak in terms of "topic", "channel", and "config".
```

### Directory Structure

```
dinopedia/                          (repo root — could be renamed to "content-factory")
├── channels/
│   ├── dinopedia/
│   │   ├── config.json             # Channel identity, prompts, voice, schedule
│   │   ├── plan.json               # Content queue
│   │   ├── data/
│   │   │   └── topics.json         # 50+ dinosaurs
│   │   └── assets/
│   │       ├── bg_music.mp3        # Channel-specific background music
│   │       └── watermark.png       # Optional branding overlay
│   │
│   ├── spacepedia/
│   │   ├── config.json
│   │   ├── plan.json
│   │   ├── data/
│   │   │   └── topics.json         # 50+ space objects
│   │   └── assets/
│   │       └── bg_music.mp3
│   │
│   └── mythopedia/
│       └── ...
│
├── src/                            # SHARED pipeline engine (channel-agnostic)
│   ├── config.py                   # Loads channel-specific config
│   ├── generation/
│   │   ├── content_generator.py    # Reads prompt template from channel config
│   │   ├── gemini_service.py       # Unchanged (generic API wrapper)
│   │   └── shorts_extractor.py
│   ├── media/
│   │   ├── audio_generator.py      # TTS provider from channel config
│   │   ├── image_generator.py      # Visual style from channel config
│   │   ├── slide_generator.py      # Brand colors from channel config
│   │   └── video_renderer.py       # Unchanged
│   ├── distribution/
│   │   └── youtube_uploader.py     # Reads credentials from channel config
│   ├── agents/
│   │   ├── generator_agent.py
│   │   └── reviewer_agent.py
│   └── data/
│       ├── topic_db.py             # Renamed from dinosaur_db.py (generic)
│       └── plan.py                 # Accepts plan_file path parameter
│
├── run_steps.py                    # Accepts --channel flag
├── output/
│   ├── dinopedia/                  # Per-channel output
│   │   └── media/trex/...
│   └── spacepedia/
│       └── media/black_hole/...
│
└── .github/workflows/
    └── daily-generation.yml        # Matrix strategy
```

## Detailed Design

### 1. Channel Config Schema

```json
{
  "channel_id": "dinopedia",
  "channel_name": "Dinopedia 🦕",
  "niche": "dinosaurs and prehistoric life",
  "youtube_category": "27",
  
  "voice": {
    "provider": "gemini",
    "persona": "Enthusiastic science educator, warm and engaging...",
    "prebuilt_voice_id": "Kore",
    "speed": "medium",
    "language": "en"
  },
  
  "visuals": {
    "provider": "gemini",
    "style": "Cinematic, photorealistic, dramatic lighting",
    "color_palette": ["#1a1a2e", "#16213e", "#0f3460", "#e94560"],
    "thumbnail_style": "Bold, vivid, dramatic dinosaur close-up"
  },
  
  "content": {
    "article_word_range": [800, 1200],
    "prompt_template": "You are a world-class science writer specializing in {niche}...",
    "tone": "fun, educational, slightly dramatic",
    "target_audience": "curious adults and older teens"
  },
  
  "schedule": {
    "long_video_interval_hours": 24,
    "shorts_per_cycle": 2
  },
  
  "credentials": {
    "youtube_secrets_env": "DINOPEDIA_YT_SECRETS",
    "youtube_creds_env": "DINOPEDIA_YT_CREDS"
  },
  
  "paths": {
    "data_file": "channels/dinopedia/data/topics.json",
    "plan_file": "channels/dinopedia/plan.json",
    "assets_dir": "channels/dinopedia/assets",
    "output_dir": "output/dinopedia"
  }
}
```

### 2. Config Loading

```python
# src/config.py
from pathlib import Path
import json

def load_channel_config(channel_id: str) -> dict:
    """Load channel-specific configuration."""
    config_path = Path(f"channels/{channel_id}/config.json")
    if not config_path.exists():
        raise FileNotFoundError(f"Channel config not found: {config_path}")
    
    with open(config_path) as f:
        config = json.load(f)
    
    # Validate required fields
    required = ["channel_id", "channel_name", "niche", "voice", "visuals", "paths"]
    for field in required:
        if field not in config:
            raise ValueError(f"Missing required config field: {field}")
    
    return config
```

### 3. CLI Changes

```bash
# Run all steps for a specific channel
python run_steps.py all --channel=dinopedia

# Run a specific step for a specific channel
python run_steps.py step1 --channel=spacepedia

# Dry run for a new channel
python run_steps.py all --channel=mythopedia --dry-run
```

### 4. GitHub Actions Matrix

```yaml
jobs:
  generate:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      max-parallel: 3
      matrix:
        channel:
          - dinopedia
          - spacepedia

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - run: sudo apt-get update && sudo apt-get install -y ffmpeg
      - run: pip install -r requirements.txt

      - name: 🚀 Generate for ${{ matrix.channel }}
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          echo "${{ secrets[format('{0}_YT_SECRETS', matrix.channel)] }}" | base64 --decode > client_secrets.json
          echo "${{ secrets[format('{0}_YT_CREDS', matrix.channel)] }}" | base64 --decode > credentials.json
          python run_steps.py all --channel=${{ matrix.channel }}

      - name: 💾 Commit
        if: success()
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email 'github-actions[bot]@users.noreply.github.com'
          git add channels/${{ matrix.channel }}/plan.json
          git diff --cached --quiet || git commit -m "feat(${{ matrix.channel }}): daily generation"
          git push
```

### 5. Migration Plan (Dinopedia → channels/dinopedia/)

| Current Location | New Location |
|-----------------|-------------|
| `data/dinosaurs.json` | `channels/dinopedia/data/topics.json` |
| `dinopedia_plan.json` | `channels/dinopedia/plan.json` |
| `assets/music/bg_music.mp3` | `channels/dinopedia/assets/bg_music.mp3` |
| `assets/fonts/` | `assets/fonts/` (stays shared) |
| `output/media/trex/` | `output/dinopedia/media/trex/` |

## Files to Change

| Action | File | Change |
|--------|------|--------|
| **MODIFY** | `src/config.py` | Add `load_channel_config()`, channel-aware API key loading |
| **MODIFY** | `src/distribution/youtube_uploader.py` | Read credentials env vars from config |
| **MODIFY** | `run_steps.py` | Add `--channel` flag, pass config through pipeline |
| **NEW** | `channels/dinopedia/config.json` | Dinopedia channel configuration |
| **NEW** | `channels/spacepedia/config.json` | Spacepedia channel configuration |

## Architectural Decisions & Refinements

Based on review iterations, the following multi-channel engineering patterns are finalized:

### 1. Repository Re-creation & Transition (Q1 Resolution)
*   **Decision**: A completely new repository titled `Multi Channel Content Factory` will be created. The original `dinopedia` repository will remain untouched as a historical baseline. All future development, scheduling, and multi-channel orchestration will occur in the new workspace.

### 2. Isolated API Key Management (Q2 Resolution)
*   **Decision**: Every channel uses its own isolated Gemini API key.
*   **Engineering Implementation**:
    *   The channel config defines the environment variable name holding the key:
        `"api_key_env_var": "SPACEPEDIA_GOOGLE_API_KEY"`
    *   At initialization, `src/config.py` reads this variable name from the config, loads its value from the system environment/`.env`, and uses it to construct the isolated Gemini `genai.Client` for that run cycle.

### 3. Dynamic Plan Queue Scheduling (Q3 Resolution)
*   **Decision**: We will not pre-seed static topic databases (like `topics.json` files with 50+ static entries).
*   **Engineering Implementation**:
    *   Topic planning is fully dynamic. The **Daily Research Producer Agent** performs active scrape research, identifies trending opportunities, and appends the script/prompt configs for approved topics directly to the channel's `plan.json` queue.
    *   The media generation engine consumes these dynamic items sequentially, eliminating static inventory databases.

---

## Acceptance Criteria

- [ ] Pipeline runs with `--channel=dinopedia` and produces identical output to current
- [ ] Adding a new channel requires only: new config.json + plan.json
- [ ] No channel-specific logic in `src/` (fully config-driven)
- [ ] Each channel loads its specific Google API key dynamically via environment variables configured in config.json
- [ ] GitHub Actions matrix runs channels in parallel
- [ ] Per-channel credential management via environment variables
- [ ] Backward compatibility: running without `--channel` defaults to `dinopedia`
