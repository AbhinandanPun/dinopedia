# Spec 06: Trend Research Producer Agent

> **Status**: 📝 Draft  
> **Priority**: 🔵 P3 (Autonomous topic discovery)  
> **Estimated Effort**: 1-2 days  
> **Dependencies**: Spec 05 (Multi-Channel) — needs channel config to know which niches to research

---

## Problem Statement

Currently, the content queue is a **static JSON file** (`dinopedia_plan.json`) with 24 hardcoded dinosaurs. Once all 24 are done, the pipeline stops. There is no mechanism to:
- Discover new trending topics within a niche
- Respond to breaking news (e.g., new dinosaur discovery)
- Identify new niches worth creating channels for
- Replenish the content queue automatically

## Proposed Solution

Build a **Producer Agent** that runs on two cadences:
1. **Daily**: Research trending topics for existing channels → propose today's hot topics → owner approves/automates → added to plan
2. **Monthly**: Research potential new niches → propose new channel ideas → owner decides whether to create

This is a genuine **agentic AI** use case because it requires judgment, exploration, and adapting to ambiguous real-world signals.

### Agent Architecture

```mermaid
flowchart TD
    subgraph DailyRun["Daily: Topic Discovery"]
        W1["Read channel configs"] --> W2["Search trending sources"]
        W2 --> W3["Filter by niche relevance"]
        W3 --> W4["Score by engagement potential"]
        W4 --> W5["Generate topic proposals"]
        W5 --> W6["Save report for owner review"]
    end

    subgraph MonthlyRun["Monthly: Niche Discovery"]
        M1["Scan broad trends"] --> M2["Evaluate competition level"]
        M2 --> M3["Estimate content potential"]
        M3 --> M4["Propose 2-3 new channel ideas"]
        M4 --> M5["Save report for owner review"]
    end

    subgraph OwnerFlow["Owner Review"]
        O1["Read daily/monthly report"] --> O2{"Decision"}
        O2 -->|"Approve topics"| O3["Add to channel plan.json"]
        O2 -->|"Approve niche"| O4["Owner creates channel manually"]
        O2 -->|"Reject"| O5["Skip / Archive"]
    end

    W6 --> O1
    M5 --> O1

    style DailyRun fill:#553c9a,stroke:#6b46c1,color:#e2e8f0
    style MonthlyRun fill:#2c5282,stroke:#3182ce,color:#e2e8f0
    style OwnerFlow fill:#744210,stroke:#d69e2e,color:#e2e8f0
```

## Detailed Design

### 1. Data Sources for Trend Research

| Source | What It Provides | Access Method |
|--------|-----------------|---------------|
| **Google Trends** | Search volume trends, rising queries | `pytrends` library (free) |
| **YouTube Trending** | Top videos in category | YouTube Data API (already have) |
| **Reddit** | Niche community engagement | Reddit API (free tier) |
| **Wikipedia** | "In the news" / recent discoveries | Web scraping (free) |
| **Google News** | Breaking news in niche | Gemini web search grounding |

### 2. Daily Topic Discovery

```python
class ProducerAgent:
    """Discovers trending topics for existing channels."""
    
    def daily_research(self, channel_config: dict) -> TopicReport:
        niche = channel_config["niche"]
        existing_topics = self._load_existing_plan(channel_config)
        
        # Step 1: Gather signals
        trends = self._search_google_trends(niche)
        youtube_hot = self._search_youtube_trending(niche)
        reddit_buzz = self._search_reddit(niche)
        
        # Step 2: Synthesize with Gemini (the "judgment" step)
        prompt = f"""
        You are a content strategist for a YouTube channel about {niche}.
        
        Here are today's signals:
        - Google Trends: {trends}
        - YouTube Trending: {youtube_hot}
        - Reddit Buzz: {reddit_buzz}
        
        Already covered topics (DO NOT suggest these): {existing_topics}
        
        Suggest 1-3 new video topics. For each:
        1. Title (click-worthy, YouTube-optimized)
        2. Description (2-3 sentences explaining the angle)
        3. Thumbnail concept (visual description)
        4. Urgency (evergreen / trending / breaking)
        5. Estimated engagement score (1-10)
        
        Prioritize topics that are trending NOW but not yet saturated.
        Return as JSON array.
        """
        
        proposals = generate_content(prompt)
        
        return TopicReport(
            channel_id=channel_config["channel_id"],
            generated_at=datetime.utcnow().isoformat(),
            proposals=json.loads(clean_json(proposals)),
            sources_checked=["google_trends", "youtube", "reddit"]
        )
```

### 3. Topic Proposal Format

Each proposal in the daily report:

```json
{
  "topic_id": "spinosaurus_swimming",
  "title": "🦕 Scientists JUST Proved Spinosaurus Could SWIM! Here's How",
  "description": "A 2026 study from University of Chicago used CT scans to confirm Spinosaurus had dense bones for buoyancy control, making it the only known swimming dinosaur. This is breaking paleontology news.",
  "thumbnail_concept": "Dramatic underwater scene of Spinosaurus diving after fish, blue-green water, realistic rendering",
  "urgency": "breaking",
  "engagement_score": 9,
  "sources": ["reddit.com/r/Paleontology", "Google Trends spike"]
}
```

### 4. Owner Review and Approval Flow

Reports are saved to a dedicated directory:

```
reports/
├── daily/
│   ├── 2026-06-26_dinopedia.json    # Daily proposals
│   ├── 2026-06-26_spacepedia.json
│   └── ...
└── monthly/
    └── 2026-06_niche_research.json
```

**Approval mechanism** (simple file-based):

```json
// reports/daily/2026-06-26_dinopedia.json
{
  "channel_id": "dinopedia",
  "generated_at": "2026-06-26T00:00:00Z",
  "status": "awaiting_review",
  "proposals": [
    {
      "topic_id": "spinosaurus_swimming",
      "title": "...",
      "approved": null  // Owner sets to true/false
    },
    ...
  ]
}
```

Owner edits the JSON, sets `approved: true` or `approved: false`, and commits. A separate pipeline step reads approved topics and adds them to the channel's `plan.json`.

### 5. Monthly Niche Discovery

```python
def monthly_niche_research(self) -> NicheReport:
    """Discover potential new channel niches."""
    
    prompt = """
    You are a YouTube channel strategist. Research and propose 3 new 
    educational YouTube channel ideas.
    
    Requirements:
    - Each niche must have 100+ potential video topics
    - The niche should be growing (not saturated)
    - Factual/educational (not opinion-based)
    - Suitable for AI-generated content (factual, visual)
    
    For each niche, provide:
    1. Channel name suggestion
    2. Niche description
    3. Target audience
    4. Sample topics (10 examples)
    5. Competition level
    6. Growth potential (1-10)
    7. Content sustainability
    """
    
    return generate_content(prompt)
```

### 6. GitHub Actions Schedule

```yaml
# .github/workflows/trend-research.yml
name: Daily Trend Research

on:
  schedule:
    - cron: '0 6 * * *'  # Every day at 6 AM UTC
  workflow_dispatch:

jobs:
  research:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        channel: [dinopedia, spacepedia]
    
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      
      - name: 🔍 Research trends for ${{ matrix.channel }}
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: python -m src.agents.producer_agent daily --channel=${{ matrix.channel }}
      
      - name: 💾 Commit report
        run: |
          git config user.name 'github-actions[bot]'
          git config user.email 'github-actions[bot]@users.noreply.github.com'
          git add reports/
          git diff --cached --quiet || git commit -m "research: daily trends for ${{ matrix.channel }}"
          git push
```

## Files to Change

| Action | File | Change |
|--------|------|--------|
| **NEW** | `src/agents/producer_agent.py` | Trend research agent |
| **NEW** | `src/agents/trend_sources.py` | Google Trends, Reddit, YouTube API wrappers |
| **NEW** | `.github/workflows/trend-research.yml` | Daily/monthly research schedule |
| **MODIFY** | `run_steps.py` | Add step to ingest approved topics into plan |
| **MODIFY** | `requirements.txt` | Add `pytrends`, `praw` (Reddit) |

## Cost Estimate

| Item | Cost per Run |
|------|-------------|
| Gemini: Trend synthesis (per channel) | ~$0.01 |
| YouTube Data API: Trending search | 100 quota units |
| Reddit API | Free |
| Google Trends (pytrends) | Free |
| **Total monthly (5 channels)** | **~$1.50** |

## Architectural Decisions & Refinements

Based on review iterations, the following scheduling and review patterns are finalized:

### 1. Content Staging Dashboard UI (Q1 Resolution)
*   **Decision**: A simple local dashboard UI will be created for daily review. Notifications containing direct review links will be sent to the owner via phone/email.
*   **Engineering Implementation**:
    *   **Dashboard Tech Stack**: A lightweight local web app will be served via **FastAPI** (`src/dashboard/`). It will render a premium, dark-themed responsive dashboard displaying the generated scripts, visual prompts, and metadata for each channel.
    *   **Interactive Review Actions**: The owner can click "Approve" or "Reject" buttons for each of the 3 proposed daily topics. Approving a topic calls a local API endpoint that updates the channel's status in `plan.json`.
    *   **Notification Integration**: Once the daily research agent completes its run, it triggers a notification via the Notification Manager (configured in Spec 03) sending a link directly to the local dashboard host.

### 2. Prioritized Backlog & Intelligent Bypass (Q2 Resolution)
*   **Decision**: Multiple topics can be approved from the daily suggestions. The highest-priority topic is processed first; others are stored as a backlog. Daily research is skipped for channels with pre-approved content.
*   **Engineering Implementation**:
    *   **Priority Scores**: The daily agent scores proposals (1-10) based on trend alignment, worthiness, uniqueness, and engagement potential.
    *   **Backlog Execution**: If the owner approves all 3 topics, the pipeline selects the single highest-scoring topic for the next day's video creation. The remaining 2 approved topics are added to the queue's backlog as `pending_approved`.
    *   **Intelligent Research Bypass**: The daily research script checks the backlog first. If `plan.json` contains any `pending_approved` topics, the agent skips running new scrapes/research for that channel, preserving API credits and tokens.

### 3. Suggestion Volume (Q3 Resolution)
*   **Decision**: The Daily Producer Agent will propose exactly **3 topics** per channel run.

---

## Acceptance Criteria

- [ ] Daily agent runs automatically every day via GitHub Actions
- [ ] Produces a structured daily report with exactly 3 topic proposals per channel
- [ ] Each proposal includes title, description, thumbnail concept, and a priority score (1-10)
- [ ] A local FastAPI Content Staging Dashboard is implemented with a responsive UI to approve/reject topics
- [ ] Approved topics are added to `plan.json` and sorted automatically by priority score
- [ ] The media pipeline processes only the highest-scoring approved topic per run
- [ ] Remaining approved topics are cached in the backlog queue
- [ ] Daily research agent bypasses query scrapes if the channel already has approved queue backlog
- [ ] Monthly niche discovery report generated on the 1st of each month
- [ ] Duplicate detection: never suggests topics already in the plan or channel archive
