"""
Manual step-by-step pipeline runner for Dinopedia.

Usage:
    python run_steps.py list                          # Show all steps
    python run_steps.py step1                         # Run Step 1 only
    python run_steps.py step1 --dry-run               # Dry-run (skip API calls)
    python run_steps.py step1 --dino velociraptor     # Pick a specific dinosaur
    python run_steps.py all                           # Run all steps sequentially
    python run_steps.py all --dry-run                 # Dry-run entire pipeline
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─── Helpers ────────────────────────────────────────────────────────────────

def _banner(msg):
    sep = "=" * 60
    print(f"\n{sep}\n  {msg}\n{sep}")

def _ok(msg):
    print(f"  [OK] {msg}")

def _skip(msg):
    print(f"  [SKIP] {msg}")

def _fail(msg):
    print(f"  [FAIL] {msg}")

def _info(msg):
    print(f"  [INFO] {msg}")

def _resolve_dinosaur(args):
    """Resolve which dinosaur to process."""
    from src.data.dinosaur_db import get_dinosaur
    from src.data.plan import get_pending_dinosaur

    if args.dino:
        dino_id = args.dino
        dino = get_dinosaur(dino_id)
        _info(f"Using specified dinosaur: {dino['common_name']} (ID: {dino_id})")
    else:
        pending = get_pending_dinosaur()
        if not pending:
            _info("No pending dinosaurs in plan. Use --dino <id> to specify one.")
            return None, None
        dino_id = pending["id"]
        dino = get_dinosaur(dino_id)
        _info(f"Next pending dinosaur: {dino['common_name']} (ID: {dino_id})")
    return dino_id, dino


STAGING_DIR = Path("output/.staging")

def _save_staging(dino_id, result):
    """Save step result to staging file for cross-step persistence."""
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    staging_path = STAGING_DIR / f"{dino_id}_latest.json"
    with open(staging_path, 'w') as f:
        # Only persist serializable fields
        data = {"dino_id": result.get("dino_id"), "content": result.get("content")}
        json.dump(data, f, indent=2)
    _info(f"Staged result to: {staging_path}")

def _load_staging(dino_id):
    """Load step result from staging file."""
    staging_path = STAGING_DIR / f"{dino_id}_latest.json"
    if staging_path.exists():
        with open(staging_path) as f:
            data = json.load(f)
        _info(f"Loaded staged result from: {staging_path}")
        return data
    return None

def _get_latest_article(dino_id):
    """Find the most recent article JSON for a dinosaur (staging first, then saved articles)."""
    # Check staging first
    staged = _load_staging(dino_id)
    if staged and staged.get("content"):
        return staged["content"], "staging"

    # Fall back to saved articles
    articles_dir = Path("output/articles")
    if not articles_dir.exists():
        return None
    matches = sorted(articles_dir.glob(f"{dino_id}_*.json"), reverse=True)
    if not matches:
        return None
    with open(matches[0]) as f:
        return json.load(f), matches[0]


# ─── Step Definitions ──────────────────────────────────────────────────────

def step1_generate_content(args):
    """Step 1: Generate article content via Gemini API."""
    _banner("STEP 1 — Generate Article Content (Gemini)")

    dino_id, dino = _resolve_dinosaur(args)
    if not dino:
        return None

    if args.dry_run:
        _skip("DRY RUN — Skipping Gemini API call")
        _info(f"Would call Gemini 2.5 Flash with prompt for: {dino['common_name']}")
        from src.generation.prompts import get_article_prompt
        prompt = get_article_prompt(dino)
        _info(f"Prompt length: {len(prompt)} chars")
        _info(f"Prompt preview:\n{prompt[:200]}...")

        # Create a mock content for downstream steps
        mock_content = {
            "article": f"[DRY RUN] This is a placeholder article about {dino['common_name']} ({dino['scientific_name']}). "
                       f"It lived during the {dino['period']} period ({dino['period_years']}). "
                       f"Key facts: {', '.join(dino['key_facts'])}. " * 10,
            "social_snippet": f"Discover {dino['common_name']}, the {dino['diet'].lower()} dinosaur from the {dino['period']}! #DryRun",
            "hashtags": ["#dinosaurs", "#paleontology", "#DryRun", "#dinopedia", "#science"]
        }
        return {"dino_id": dino_id, "content": mock_content, "dry_run": True}

    # Real run
    from src.generation.gemini_service import init_gemini
    from src.generation.content_generator import generate_dinosaur_content

    init_gemini()
    _info("Gemini client initialized")

    content = generate_dinosaur_content(dino_id)
    _ok(f"Article generated: {len(content['article'])} chars")
    _ok(f"Social snippet: {len(content['social_snippet'])} chars")
    _ok(f"Hashtags: {', '.join(content['hashtags'])}")

    result = {"dino_id": dino_id, "content": content, "dry_run": False}
    _save_staging(dino_id, result)
    return result


def step2_save_article(args, prev_result=None):
    """Step 2: Save generated content to output/articles/."""
    _banner("STEP 2 — Save Article to Disk")

    dino_id = prev_result["dino_id"] if prev_result else None
    content = prev_result["content"] if prev_result else None

    if not content:
        dino_id, _ = _resolve_dinosaur(args)
        if not dino_id:
            return None
        result = _get_latest_article(dino_id)
        if result:
            content, path = result
            _info(f"Loaded existing article from: {path}")
        else:
            _fail(f"No article found for '{dino_id}'. Run step1 first.")
            return None

    if args.dry_run:
        _skip("DRY RUN — Would save to output/articles/ and output/metadata/")
        _info(f"  Article JSON: output/articles/{dino_id}_<timestamp>.json")
        _info(f"  Markdown:     output/articles/{dino_id}_<timestamp>.md")
        _info(f"  Metadata:     output/metadata/{dino_id}_<timestamp>.json")
        return {"dino_id": dino_id, "content": content, "dry_run": True}

    from src.data.repository import save_article
    result = save_article(dino_id, content)
    _ok(f"JSON:     {result['json']}")
    _ok(f"Markdown: {result['markdown']}")
    _ok(f"Metadata: {result['metadata']}")

    return {"dino_id": dino_id, "content": content, "saved": result, "dry_run": False}


def step3_generate_slides(args, prev_result=None):
    """Step 3: Generate slide images from article content."""
    _banner("STEP 3 — Generate Slide Images")

    dino_id, content = None, None
    if prev_result:
        dino_id = prev_result.get("dino_id")
        content = prev_result.get("content")

    if not content:
        dino_id, _ = _resolve_dinosaur(args)
        if not dino_id:
            return None
        result = _get_latest_article(dino_id)
        if result:
            content, path = result
            _info(f"Loaded article from: {path}")
        else:
            _fail(f"No article found for '{dino_id}'. Run step1 first.")
            return None

    # Split article into slide chunks
    article_text = content["article"]
    sentences = [s.strip() for s in article_text.replace("\n", " ").split(".") if s.strip()]
    chunk_size = max(1, len(sentences) // 6)
    slides = []
    for i in range(0, len(sentences), chunk_size):
        chunk = ". ".join(sentences[i:i + chunk_size]) + "."
        slides.append({
            "title": f"Part {len(slides) + 1}",
            "content": chunk
        })
    # Cap at 8 slides max
    slides = slides[:8]
    _info(f"Split article into {len(slides)} slides")

    output_dir = Path(f"output/media/{dino_id}/slides")

    if args.dry_run:
        _skip("DRY RUN — Would generate slide images")
        for i, slide in enumerate(slides):
            _info(f"  Slide {i+1}: \"{slide['title']}\" ({len(slide['content'])} chars)")
        _info(f"  Output dir: {output_dir}")
        return {"dino_id": dino_id, "content": content, "slides": slides, "slide_paths": [], "dry_run": True}

    from src.media.slide_generator import generate_visuals
    slide_paths = []
    for i, slide in enumerate(slides):
        path = generate_visuals(
            output_dir=output_dir,
            video_type="long",
            slide_content=slide,
            slide_number=i + 1,
            total_slides=len(slides)
        )
        slide_paths.append(path)
        _ok(f"Slide {i+1}: {path}")

    # Generate thumbnail
    thumb_path = generate_visuals(
        output_dir=output_dir,
        video_type="long",
        thumbnail_title=content.get("social_snippet", dino_id)[:60]
    )
    _ok(f"Thumbnail: {thumb_path}")

    return {
        "dino_id": dino_id, "content": content, "slides": slides,
        "slide_paths": slide_paths, "thumbnail_path": thumb_path, "dry_run": False
    }


def step4_generate_audio(args, prev_result=None):
    """Step 4: Generate TTS audio for each slide."""
    _banner("STEP 4 — Generate Audio (TTS)")

    dino_id = prev_result.get("dino_id") if prev_result else None
    slides = prev_result.get("slides") if prev_result else None

    if not slides:
        dino_id, _ = _resolve_dinosaur(args)
        if not dino_id:
            return None
        # Try to rebuild slides from article
        result = _get_latest_article(dino_id)
        if result:
            content, _ = result
            article_text = content["article"]
            sentences = [s.strip() for s in article_text.replace("\n", " ").split(".") if s.strip()]
            chunk_size = max(1, len(sentences) // 6)
            slides = []
            for i in range(0, len(sentences), chunk_size):
                chunk = ". ".join(sentences[i:i + chunk_size]) + "."
                slides.append({"title": f"Part {len(slides) + 1}", "content": chunk})
            slides = slides[:8]
        else:
            _fail(f"No article found for '{dino_id}'. Run step1 first.")
            return None

    output_dir = Path(f"output/media/{dino_id}/audio")

    if args.dry_run:
        _skip("DRY RUN — Would generate TTS audio")
        for i, slide in enumerate(slides):
            text_preview = f"{slide['title']}. {slide['content'][:50]}..."
            _info(f"  Audio {i+1}: \"{text_preview}\"")
        _info(f"  Output dir: {output_dir}")
        if prev_result:
            prev_result["audio_paths"] = []
        return prev_result or {"dino_id": dino_id, "slides": slides, "audio_paths": [], "dry_run": True}

    from src.media.audio_generator import generate_slide_audio
    audio_paths = generate_slide_audio(slides, output_dir)
    for i, p in enumerate(audio_paths):
        _ok(f"Audio {i+1}: {p}")

    if prev_result:
        prev_result["audio_paths"] = audio_paths
        return prev_result
    return {"dino_id": dino_id, "slides": slides, "audio_paths": audio_paths, "dry_run": False}


def step5_render_video(args, prev_result=None):
    """Step 5: Render final video from slides + audio."""
    _banner("STEP 5 — Render Video (MoviePy)")

    dino_id = prev_result.get("dino_id") if prev_result else None
    slide_paths = prev_result.get("slide_paths", []) if prev_result else []
    audio_paths = prev_result.get("audio_paths", []) if prev_result else []

    if not dino_id:
        dino_id, _ = _resolve_dinosaur(args)
        if not dino_id:
            return None

    if not slide_paths:
        slides_dir = Path(f"output/media/{dino_id}/slides")
        if slides_dir.exists():
            slide_paths = sorted([p for p in slides_dir.glob("slide_*.png")])
            
    if not audio_paths:
        audio_dir = Path(f"output/media/{dino_id}/audio")
        if audio_dir.exists():
            audio_paths = sorted([p for p in audio_dir.glob("slide_*.wav")])

    output_path = Path(f"output/media/{dino_id}/{dino_id}_video.mp4")

    if args.dry_run:
        _skip("DRY RUN — Would render video")
        _info(f"  Slides: {len(slide_paths)} images")
        _info(f"  Audio:  {len(audio_paths)} clips")
        _info(f"  Output: {output_path}")
        if prev_result:
            prev_result["video_path"] = str(output_path)
        return prev_result or {"dino_id": dino_id, "video_path": str(output_path), "dry_run": True}

    if not slide_paths or not audio_paths:
        _fail("Need slide_paths and audio_paths. Run step3 and step4 first.")
        return prev_result

    from src.media.video_renderer import create_video
    create_video(slide_paths, audio_paths, output_path, video_type="long")
    _ok(f"Video rendered: {output_path}")

    if prev_result:
        prev_result["video_path"] = str(output_path)
        return prev_result
    return {"dino_id": dino_id, "video_path": str(output_path), "dry_run": False}


def step6_upload_youtube(args, prev_result=None):
    """Step 6: Upload video to YouTube."""
    _banner("STEP 6 — Upload to YouTube")

    dino_id = prev_result.get("dino_id") if prev_result else None
    video_path = prev_result.get("video_path") if prev_result else None
    content = prev_result.get("content", {}) if prev_result else {}
    thumbnail_path = prev_result.get("thumbnail_path") if prev_result else None

    if not dino_id:
        dino_id, _ = _resolve_dinosaur(args)

    if not video_path:
        video_path = f"output/media/{dino_id}/{dino_id}_video.mp4"

    # If run standalone, reconstruct content and thumbnail_path from disk
    if not prev_result:
        staged = _load_staging(dino_id)
        if staged:
            content = staged.get("content", {})
        
        thumb_file = Path(f"output/media/{dino_id}/slides/thumbnail.png")
        if thumb_file.exists():
            thumbnail_path = str(thumb_file)

    title = f"Dinopedia: {dino_id.replace('_', ' ').title()}"
    description = content.get("social_snippet", f"Learn about {dino_id}!")
    tags = ",".join(content.get("hashtags", ["#dinosaurs", "#paleontology"]))

    if args.dry_run:
        _skip("DRY RUN — Would upload to YouTube")
        _info(f"  Video:       {video_path}")
        _info(f"  Title:       {title}")
        _info(f"  Description: {description[:80]}...")
        _info(f"  Tags:        {tags}")
        _info(f"  Thumbnail:   {thumbnail_path or 'None'}")
        return prev_result or {"dino_id": dino_id, "dry_run": True}

    if not Path(video_path).exists():
        _fail(f"Video file not found: {video_path}. Run step5 first.")
        return prev_result

    from src.distribution.youtube_uploader import upload_to_youtube
    video_id = upload_to_youtube(video_path, title, description, tags, thumbnail_path)
    _ok(f"Uploaded! YouTube Video ID: {video_id}")
    _ok(f"URL: https://www.youtube.com/watch?v={video_id}")

    return prev_result


def step7_mark_complete(args, prev_result=None):
    """Step 7: Mark dinosaur as complete in the plan."""
    _banner("STEP 7 — Mark Complete in Plan")

    dino_id = prev_result.get("dino_id") if prev_result else None
    if not dino_id:
        dino_id, _ = _resolve_dinosaur(args)
        if not dino_id:
            return None

    if args.dry_run:
        _skip(f"DRY RUN — Would mark '{dino_id}' as complete in dinopedia_plan.json")
        return prev_result

    from src.data.plan import mark_complete
    mark_complete(dino_id)
    _ok(f"Marked '{dino_id}' as complete in dinopedia_plan.json")
    return prev_result


# ─── Step Registry ─────────────────────────────────────────────────────────

STEPS = {
    "step1": ("Generate Article Content (Gemini API)", step1_generate_content),
    "step2": ("Save Article to Disk",                 step2_save_article),
    "step3": ("Generate Slide Images (PIL)",          step3_generate_slides),
    "step4": ("Generate Audio / TTS (gTTS)",          step4_generate_audio),
    "step5": ("Render Video (MoviePy)",               step5_render_video),
    "step6": ("Upload to YouTube",                    step6_upload_youtube),
    "step7": ("Mark Complete in Plan",                 step7_mark_complete),
}


def cmd_list(args):
    """List all available steps."""
    _banner("Dinopedia Pipeline Steps")
    for key, (desc, _) in STEPS.items():
        print(f"  {key}  ->  {desc}")
    print()
    print("  Usage:")
    print("    python run_steps.py <step>              # Run a specific step")
    print("    python run_steps.py <step> --dry-run    # Simulate without API calls")
    print("    python run_steps.py <step> --dino trex  # Specify dinosaur ID")
    print("    python run_steps.py all                 # Run all steps sequentially")
    print("    python run_steps.py all --dry-run       # Dry-run all steps")
    print()


def cmd_all(args):
    """Run all steps sequentially."""
    _banner("Running ALL Steps")
    result = None
    step_funcs = [
        step1_generate_content,
        step2_save_article,
        step3_generate_slides,
        step4_generate_audio,
        step5_render_video,
        step6_upload_youtube,
        step7_mark_complete,
    ]
    for fn in step_funcs:
        try:
            result = fn(args, result) if result else fn(args)
        except Exception as e:
            _fail(f"Step {fn.__name__} failed: {e}")
            if not args.dry_run:
                raise
            break

    _banner("Pipeline Complete!" if not args.dry_run else "Dry Run Complete!")


# ─── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Dinopedia — Manual Step-by-Step Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "step",
        choices=list(STEPS.keys()) + ["list", "all"],
        help="Which step to run (or 'list' / 'all')"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate without making API calls or writing files"
    )
    parser.add_argument(
        "--dino", type=str, default=None,
        help="Dinosaur ID to process (e.g. trex, velociraptor). Defaults to next pending."
    )

    args = parser.parse_args()

    if args.step == "list":
        cmd_list(args)
    elif args.step == "all":
        cmd_all(args)
    else:
        desc, fn = STEPS[args.step]
        _banner(f"Running: {args.step} — {desc}")
        fn(args)


if __name__ == "__main__":
    main()
