# Spec 04: YouTube Shorts Pipeline

> **Status**: 📝 Draft  
> **Priority**: 🟠 P1 (High — 3x content output)  
> **Estimated Effort**: 4-6 hours  
> **Dependencies**: Spec 01 (TTS), Spec 02 (Visuals)

---

## Problem Statement

Currently, the pipeline generates only **1 long-form video** per cycle. YouTube Shorts are the fastest-growing content format and the primary discovery mechanism for new channels. Not generating Shorts means:
- Missing 50%+ of potential views (Shorts algorithm is extremely generous to new channels)
- Losing cross-promotion opportunity (Shorts viewers → Long-form subscribers)
- Under-utilizing content (each article has enough material for multiple Shorts)

## Proposed Solution

Generate **2 YouTube Shorts alongside every long-form video**, using the same article content. Each Short is a focused 30-45 second highlight extracted from the full article.

### Content Flow

```mermaid
flowchart TD
    A["ContentBundle - full article, 8 slides"] --> B["Extract Shorts Material"]
    B --> C["Short 1: Most Shocking Fact"]
    B --> D["Short 2: Did You Know"]
    
    A --> E["Long Video Pipeline - 1920x1080"]
    C --> F["Short Video Pipeline - 1080x1920"]
    D --> F
    
    E --> G["Upload: Long Video"]
    F --> H["Upload: Short 1"]
    F --> I["Upload: Short 2"]

    style A fill:#2d3748,color:#e2e8f0
    style C fill:#553c9a,color:#e2e8f0
    style D fill:#553c9a,color:#e2e8f0
    style E fill:#2c5282,color:#e2e8f0
    style F fill:#2c5282,color:#e2e8f0
    style G fill:#22543d,color:#e2e8f0
    style H fill:#22543d,color:#e2e8f0
    style I fill:#22543d,color:#e2e8f0
```

## Detailed Design

### 1. Short Content Extraction

Use Gemini to intelligently select the two most "shareable" facts from the article:

```python
def extract_shorts_content(article: str, topic_name: str) -> list[dict]:
    """Extract 2 short-form content pieces from the full article."""
    
    prompt = f"""
    From this article about {topic_name}, extract exactly 2 standalone 
    short-form video scripts.
    
    Each short should be:
    - ONE shocking, surprising, or "wow" fact
    - 40-60 words maximum (will become 20-30 seconds of narration)
    - Self-contained (viewer needs no context from the full video)
    - Starts with a hook question or bold statement
    
    Format as JSON:
    [
      {{
        "type": "shocking_fact",
        "hook": "Did you know T-Rex could bite with 12,800 newtons of force?",
        "script": "That's enough to crush a car...",
        "visual_prompt": "A dramatic close-up of T-Rex jaws biting down"
      }},
      {{
        "type": "did_you_know",
        "hook": "...",
        "script": "...",
        "visual_prompt": "..."
      }}
    ]
    
    Article:
    {article}
    """
    
    response = generate_content(prompt)
    return json.loads(clean_json(response))
```

### 2. Short Video Specifications

| Property | Long Video | Short Video |
|----------|-----------|-------------|
| **Resolution** | 1920×1080 (16:9) | 1080×1920 (9:16) |
| **Duration** | 2-5 minutes | 20-45 seconds |
| **Visuals** | Timeline of B-roll segments | Timeline of vertical B-roll segments |
| **Audio** | Full narration | Quick, punchy narration |
| **Music** | Background at 5% | Background at 10% (more energy) |
| **Text** | Detailed content | Large, bold, minimal center-subtitles |
| **Transitions** | Fade 0.5s | Quick cut or zoom |

### 3. Short B-Roll Timeline Assembly

Instead of drawing text onto slide cards, the engine compiles a short-form vertical video:

```python
def assemble_short_timeline(content: dict, channel_config: dict) -> list[dict]:
    """Assemble a vertical (9:16) visual timeline plan for a Short."""
    
    timeline = []
    # Generate vertical AI image or fetch vertical stock video
    for prompt in content.get("visual_prompts", []):
        timeline.append({
            "asset_type": "gemini_image",
            "prompt": prompt,
            "aspect_ratio": "9:16",
            "motion_effect": "zoom_in",
            "duration": 5.0
        })
    
    return timeline
```

### 4. Upload & Linking Strategy

Shorts are uploaded with `#Shorts` in the title and description, and cross-promoted back to the parent long-form video. The upload times are randomized across the day using YouTube's native API scheduling parameter:

```python
def upload_short(video_path: str, content: dict, parent_youtube_id: str, channel_config: dict) -> str:
    """Upload a Short to YouTube and link to parent long video, scheduling randomly."""
    
    title = f"{content['hook'][:90]} #Shorts"
    # Embed parent long-form video link in description
    description = f"{content['script']}\n\nWatch full video: https://youtu.be/{parent_youtube_id}\n\n#Shorts"
    
    # Calculate a random publishing timestamp within the current 24h window
    publish_time = calculate_random_publish_time()
    
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": channel_config.get("default_tags", []) + ["#Shorts"],
            "categoryId": channel_config["youtube_category"]
        },
        "status": {
            "privacyStatus": "private",  # Required for scheduled publishing
            "publishAt": publish_time.isoformat(),  # Native API scheduling
            "selfDeclaredMadeForKids": False
        }
    }
    
    return upload_video(video_path, body)
```

### 5. Pipeline Integration

```mermaid
flowchart TD
    S1["Step 1: Generate Content"] --> S2["Step 2: Save Article"]
    S2 --> S3["Step 3a: Generate Long B-Roll Plan"]
    S2 --> S3b["Step 3b: Extract Shorts Content"]
    S3b --> S3c["Step 3c: Generate Short B-Roll Plan"]
    S3 --> S4["Step 4a: Generate Long Audio"]
    S3c --> S4b["Step 4b: Generate Short Audio"]
    S4 --> S5a["Step 5a: Render Long Video"]
    S4b --> S5b["Step 5b: Render Short Videos"]
    S5a --> S6a["Step 6a: Upload Long Video"]
    S6a -->|"Get YouTube Video ID"| S6b["Step 6b: Link & Upload Shorts"]
    S6b --> S7["Step 7: Mark Complete"]

    style S3b fill:#553c9a,color:#e2e8f0
    style S3c fill:#553c9a,color:#e2e8f0
    style S4b fill:#553c9a,color:#e2e8f0
    style S5b fill:#553c9a,color:#e2e8f0
    style S6b fill:#553c9a,color:#e2e8f0
```

## Files to Change

| Action | File | Change |
|--------|------|--------|
| **MODIFY** | [run_steps.py](file:///c:/Users/User/OneDrive/Documents/Workspace/dinopedia/run_steps.py) | Add Short extraction, rendering, description linking, and upload sub-steps |
| **MODIFY** | [video_renderer.py](file:///c:/Users/User/OneDrive/Documents/Workspace/dinopedia/src/media/video_renderer.py) | Handle vertical 9:16 render layouts and B-roll timeline assembly |
| **MODIFY** | [youtube_uploader.py](file:///c:/Users/User/OneDrive/Documents/Workspace/dinopedia/src/distribution/youtube_uploader.py) | Implement randomized scheduling offsets and cross-linking descriptions |
| **NEW** | `src/generation/shorts_extractor.py` | Extract short-form B-roll and script packages from articles |

## Cost Estimate (Incremental per Video Cycle)

| Item | Cost |
|------|------|
| Gemini: Extract 2 shorts content | ~$0.002 |
| Gemini Image: 2 vertical images | ~$0.04 |
| Gemini TTS: 2 short narrations | ~$0.002 |
| Video render time (2 × 30 sec) | Negligible |
| YouTube upload quota (2 × 1,600 units) | 3,200 units |
| **Total incremental** | **~$0.044 + 3,200 quota** |

> [!WARNING]
> With 3 uploads per cycle (1 long + 2 shorts), YouTube API quota becomes the bottleneck at **~3 cycles per day** per GCP project (10,000 units ÷ 3 × 1,600 per upload ≈ 2 full cycles).

## Architectural Decisions & Refinements

Based on review iterations, the following engineering patterns are finalized for the Shorts pipeline:

### 1. Randomized Upload Pacing (Q1 Resolution)
*   **Decision**: Long-form videos and both Shorts will be uploaded to publish randomly at any time of the day.
*   **Engineering Implementation**: The pipeline will calculate a randomized publishing schedule. Long videos are scheduled randomly, Short 1 is offset by a random window of 3 to 6 hours, and Short 2 by 8 to 14 hours. We use the YouTube API's native `publishAt` property with `privacyStatus: "private"`.

### 2. Description Cross-Linking (Q2 Resolution)
*   **Decision**: Shorts descriptions must automatically link back to their parent long-form video.
*   **Engineering Implementation**: The upload process is serialized: the long-form video is uploaded first, generating its YouTube URL. The pipeline copies this URL and inserts a `"Watch the full video: https://youtu.be/{youtube_id}"` link in the metadata description of the two matching Shorts before calling their upload scripts.

### 3. Platform Standardization (Q3 Resolution)
*   **Decision**: A single standardized vertical 9:16 format will be used everywhere (YouTube, Reels, TikTok) without platform-specific variations.

---

## Acceptance Criteria

- [ ] 2 Shorts automatically generated alongside every long-form video
- [ ] Shorts use vertical 9:16 resolution (1080×1920) with timeline B-roll layouts
- [ ] Shorts are 20-45 seconds with engaging hook
- [ ] Shorts have `#Shorts` in title for YouTube auto-detection
- [ ] Shorts descriptions automatically contain the parent video link
- [ ] Upload times are randomized using YouTube's native `publishAt` schedule parameter
- [ ] Shorts content is extracted from the same article (no extra Gemini article call)
- [ ] Pipeline handles both long + shorts in a single run
- [ ] YouTube quota budget accounts for 3 uploads per cycle
