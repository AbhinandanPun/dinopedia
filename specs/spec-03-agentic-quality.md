# Spec 03: Agentic Quality Pipeline

> **Status**: 📝 Draft  
> **Priority**: 🟠 P1 (High — quality gate before upload)  
> **Estimated Effort**: 1-2 days  
> **Dependencies**: Spec 01 (TTS), Spec 02 (Visuals) should be done first

---

## Problem Statement

Currently, content flows directly from generation to upload with only basic length/format validation. There is:
- **No copyright check** — AI-generated text could inadvertently plagiarize
- **No quality review** — no assessment of engagement potential, hook strength, or pacing
- **No trend alignment** — content ignores what's currently popular
- **No platform compliance check** — no verification against YouTube/TikTok policies

The user wants an **agentic process** where:
1. A **Generator Agent** creates the content (script, audio prompt, visual prompts)
2. A **Reviewer Agent** evaluates it against copyright, trends, and quality standards
3. The owner gets a **review/approval step** during development

## Proposed Solution

Introduce a two-agent architecture within the existing pipeline. These are **lightweight LLM-based agents** (structured prompt chains with decision-making), not heavyweight autonomous agents.

### System Architecture

```mermaid
flowchart TD
    subgraph GeneratorAgent["Generator Agent"]
        G1["Read topic from plan"] --> G2["Generate article script"]
        G2 --> G3["Generate audio narration prompt"]
        G3 --> G4["Generate visual scene descriptions"]
        G4 --> G5["Generate SEO metadata"]
        G5 --> G6["Package: ContentBundle"]
    end

    subgraph ReviewerAgent["Reviewer Agent"]
        R1["Receive ContentBundle"] --> R2["Copyright Check"]
        R2 --> R3["Quality Check"]
        R3 --> R4["Platform Compliance"]
        R4 --> R5["Trend Relevance"]
        R5 --> R6{"Decision"}
        R6 -->|"APPROVED"| R7["Pass to Media Pipeline"]
        R6 -->|"NEEDS REVISION"| R8["Return feedback to Generator"]
        R6 -->|"REJECTED"| R9["Flag for owner review"]
    end

    subgraph OwnerReview["Owner Review - dev mode only"]
        O1["Review ContentBundle + Reviewer report"]
        O1 -->|"Approve"| O2["Continue to media production"]
        O1 -->|"Edit"| O3["Modify and resubmit"]
        O1 -->|"Reject"| O4["Skip this topic"]
    end

    G6 --> R1
    R8 -->|"Max 2 retries"| G2
    R7 -->|"Production mode"| MediaPipeline["Media Production"]
    R7 -->|"Dev mode"| O1
    O2 --> MediaPipeline

    style GeneratorAgent fill:#553c9a,stroke:#6b46c1,color:#e2e8f0
    style ReviewerAgent fill:#2c5282,stroke:#3182ce,color:#e2e8f0
    style OwnerReview fill:#744210,stroke:#d69e2e,color:#e2e8f0
```

## Detailed Design

### 1. ContentBundle Data Structure

The Generator Agent produces a complete content package:

```python
@dataclass
class ContentBundle:
    """Complete content package for one video."""
    topic_id: str
    topic_name: str
    channel_id: str
    
    # Script
    article: str
    social_snippet: str
    hashtags: list[str]
    
    # Audio direction
    narration_prompts: list[dict]  # Per-slide narration with emotion cues
    
    # Visual direction
    slide_descriptions: list[dict]  # Per-slide image generation prompts
    thumbnail_description: str
    
    # SEO
    youtube_title: str
    youtube_description: str
    youtube_tags: list[str]
    
    # Metadata
    generated_at: str
    generator_model: str
    
    # Review
    review_status: str = "pending"  # pending | approved | needs_revision | rejected
    review_report: dict = None
```

### 2. Generator Agent

The Generator Agent is a **structured prompt chain** (not a free-roaming agent):

```python
class GeneratorAgent:
    """Generates complete content bundles using structured prompt chains."""
    
    def generate(self, topic: dict, channel_config: dict) -> ContentBundle:
        # Step 1: Generate the article script
        article = self._generate_script(topic, channel_config)
        
        # Step 2: Generate narration prompts (how should each slide sound?)
        narration_prompts = self._generate_narration_direction(article, channel_config)
        
        # Step 3: Generate visual descriptions (what should each slide look like?)
        slide_descriptions = self._generate_visual_direction(article, channel_config)
        
        # Step 4: Generate SEO metadata
        seo = self._generate_seo(article, topic, channel_config)
        
        # Step 5: Generate thumbnail concept
        thumbnail_desc = self._generate_thumbnail_concept(topic, channel_config)
        
        return ContentBundle(
            article=article,
            narration_prompts=narration_prompts,
            slide_descriptions=slide_descriptions,
            thumbnail_description=thumbnail_desc,
            **seo
        )
    
    def revise(self, bundle: ContentBundle, feedback: dict) -> ContentBundle:
        """Revise a bundle based on Reviewer feedback."""
        # Targeted re-generation of flagged sections only
        ...
```

### 3. Reviewer Agent

The Reviewer Agent evaluates the ContentBundle across four dimensions:

```python
class ReviewerAgent:
    """Reviews content bundles for quality, originality, and compliance."""
    
    def review(self, bundle: ContentBundle) -> ReviewReport:
        scores = {}
        
        # Dimension 1: Originality / Copyright
        scores["originality"] = self._check_originality(bundle.article)
        
        # Dimension 2: Engagement Quality
        scores["quality"] = self._check_quality(bundle)
        
        # Dimension 3: Platform Compliance
        scores["compliance"] = self._check_compliance(bundle)
        
        # Dimension 4: Trend Relevance (optional)
        scores["relevance"] = self._check_relevance(bundle)
        
        # Decision
        decision = self._decide(scores)
        
        return ReviewReport(
            scores=scores,
            decision=decision,  # "approved" | "needs_revision" | "rejected"
            feedback=self._generate_feedback(scores),
            timestamp=datetime.utcnow().isoformat()
        )
```

#### Review Dimensions

| Dimension | What It Checks | How |
|-----------|---------------|-----|
| **Originality** | Plagiarism risk, generic content | Gemini prompt: "Rate originality 1-10. Flag any passages that sound like Wikipedia copy." |
| **Quality** | Hook strength, pacing, engagement | Gemini prompt: "Does the first sentence hook attention? Is the pacing varied? Would a viewer watch to the end?" |
| **Compliance** | YouTube/TikTok policy violations | Gemini prompt: "Check for: misleading claims, clickbait without delivery, age-inappropriate content, AI disclosure needed." |
| **Relevance** | Trend alignment, timeliness | Gemini prompt: "Is this topic currently interesting? Any recent news that makes this timely?" |

### 4. Owner Review Interface (Dev Mode)

During development, approved content is saved to a staging area for the owner to review:

```
output/staging/{channel_id}/{topic_id}/
├── content_bundle.json     # Full ContentBundle
├── review_report.json      # Reviewer Agent's assessment
├── preview/
│   ├── script.md           # Human-readable script
│   ├── narration_notes.md  # Audio direction summary
│   └── visual_notes.md     # Visual direction summary
└── status.json             # { "status": "awaiting_approval" }
```

The owner reviews by:
1. Reading the staged files
2. Updating `status.json` to `"approved"`, `"rejected"`, or `"needs_edit"`
3. The pipeline picks up approved bundles on the next run

> [!NOTE]
> In production mode, the Reviewer Agent's "approved" decision directly triggers media production. No owner review needed.

### 5. Retry Logic

```mermaid
flowchart TD
    G["Generator: Create Bundle"] --> R["Reviewer: Evaluate"]
    R -->|"Approved - score 7+"| Done["Proceed to media"]
    R -->|"Needs Revision - score 4-6"| Feedback["Extract feedback"]
    Feedback --> G2["Generator: Revise - attempt 2"]
    G2 --> R2["Reviewer: Re-evaluate"]
    R2 -->|"Approved"| Done
    R2 -->|"Still failing"| Skip["Flag for owner + skip topic"]

    style G fill:#553c9a,color:#e2e8f0
    style R fill:#2c5282,color:#e2e8f0
    style Done fill:#22543d,color:#e2e8f0
    style Skip fill:#9b2c2c,color:#e2e8f0
```

Maximum 2 revision attempts. If still failing, skip the topic and flag for owner review.

## Files to Change

| Action | File | Change |
|--------|------|--------|
| **NEW** | `src/agents/generator_agent.py` | Generator Agent class |
| **NEW** | `src/agents/reviewer_agent.py` | Reviewer Agent class |
| **NEW** | `src/agents/models.py` | ContentBundle, ReviewReport dataclasses |
| **MODIFY** | [run_steps.py](file:///c:/Users/User/OneDrive/Documents/Workspace/dinopedia/run_steps.py) | Integrate agents into pipeline, add staging/approval flow |
| **MODIFY** | [content_generator.py](file:///c:/Users/User/OneDrive/Documents/Workspace/dinopedia/src/generation/content_generator.py) | Delegate to GeneratorAgent |
| **NEW** | `tests/test_generator_agent.py` | Unit tests |
| **NEW** | `tests/test_reviewer_agent.py` | Unit tests |

## Cost Estimate

| Agent Call | Cost per Video |
|-----------|---------------|
| Generator: script generation | ~$0.003 |
| Generator: narration direction | ~$0.002 |
| Generator: visual direction | ~$0.002 |
| Generator: SEO metadata | ~$0.001 |
| Reviewer: full evaluation | ~$0.005 |
| Revision (50% chance) | ~$0.005 |
| **Total per video** | **~$0.02** |

## Architectural Decisions & Refinements

Based on review iterations, the following engineering patterns are finalized for the agentic quality and verification pipeline:

### 1. Developer Notification System (Q1 Resolution)
*   **Decision**: When content is staged for review in developer mode, the owner will receive a notification via email or phone message.
*   **Engineering Implementation**:
    *   We will establish a unified **Notification Manager** in `src/utils/notifier.py` supporting two notification backends configured via `.env`:
        1. **Email Notification (SMTP)**: Sends a formatted email using Python's built-in `smtplib` (configured with a standard SMTP host/password, such as Gmail App Passwords).
        2. **Webhook Notification (Discord/Telegram)**: Sends a message directly to your phone via a Discord webhook or Telegram bot request (highly recommended for instant, mobile-native push alerts).
    *   **Notification Trigger**: Once a `ContentBundle` is created and staged, the orchestrator triggers:
        `"🚀 [Dinopedia] Topic 'T-Rex' is staged and ready for your review! Reviewer Score: 7.8/10. Preview path: output/staging/dinopedia/trex/"`

### 2. Grounded Reviewer Agent (Q2 Resolution)
*   **Decision**: The Reviewer Agent evaluates the content itself, but utilizes web access to check for current trends, platform policies, and scientific updates.
*   **Engineering Implementation**:
    *   **Google Search Grounding**: We will enable Gemini's native **Google Search Tool** in the Google GenAI SDK for the Reviewer Agent. This is a clean, API-native solution that avoids brittle web-scraping libraries.
    *   **Grounded Prompts**: During evaluation, the Reviewer Agent executes grounding queries to check:
        1. *Policy Compliance*: Searches current 2026 YouTube/TikTok policies on AI-generated content disclosures and copyright boundaries.
        2. *Trend & Fact Alignment*: Searches recent discoveries related to the topic (e.g. recent fossil discoveries) to ensure the script's facts are up-to-date and highly engaging.

### 3. Strict Auto-Approval Threshold (Q3 Resolution)
*   **Decision**: The quality score must be **more than or equal to 8/10** to trigger auto-approval in production mode.
*   **Engineering Implementation**:
    *   If the Reviewer Agent scores a content bundle $\ge 8/10$ on the first run (or after revisions), it bypasses manual review (in production mode) and triggers the B-roll media rendering steps directly.
    *   If the score is between `5` and `7.9`, the Reviewer Agent sends constructive feedback back to the Generator Agent. The Generator Agent has a maximum of **2 revision attempts** to improve the score to $\ge 8/10$.
    *   If the bundle fails to reach $\ge 8/10$ after 2 revision retries, it is automatically saved to the developer staging area, and a notification is sent to the owner: *"⚠️ [Dinopedia] Topic 'Spinosaurus' failed auto-publish threshold (Score: 7.7/10). Staged for manual audit."*

---

## Acceptance Criteria

- [ ] Generator Agent produces complete ContentBundles with script, audio direction, visual direction, and SEO
- [ ] Reviewer Agent evaluates across 4 dimensions and produces a structured report
- [ ] Reviewer Agent utilizes Gemini Google Search Grounding to verify trends and policy compliance
- [ ] Max 2 revision retries before flagging for owner
- [ ] Dev mode: content staged for owner approval, and a notification is dispatched (Email/Webhook)
- [ ] Production mode: auto-approved content (Score $\ge 8/10$) goes directly to media production
- [ ] All review decisions, scores, and search sources are logged for auditability
- [ ] Pipeline gracefully handles both modes via config flag
- [ ] Notification credentials and webhook URLs are securely loaded via `.env`
