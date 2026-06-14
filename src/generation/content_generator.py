"""Orchestration layer for content generation with validation."""

from src.data.dinosaur_db import get_dinosaur
from src.generation.gemini_service import generate_dinosaur_article
from src.logger import get_logger

logger = get_logger(__name__)

def generate_dinosaur_content(dinosaur_id):
    """
    Generate content for a dinosaur.
    
    Args:
        dinosaur_id: ID of dinosaur to generate for
        
    Returns:
        dict with article, social_snippet, hashtags
    """
    # Load dinosaur
    dinosaur = get_dinosaur(dinosaur_id)
    logger.info(f"Starting content generation for {dinosaur['common_name']}")
    
    # Generate via Gemini
    content = generate_dinosaur_article(dinosaur)
    
    # Validate required fields
    required_fields = ["article", "social_snippet", "hashtags"]
    for field in required_fields:
        assert field in content, f"Missing required field: {field}"
    
    # Validate field lengths
    # 800-1200 words ≈ 4500-7000+ characters
    article_len = len(content["article"])
    assert 4000 <= article_len <= 8000, f"Article length {article_len} not in 4000-8000 range (800-1200 words)"
    
    # 180-200 characters for social snippet
    snippet_len = len(content["social_snippet"])
    assert 150 <= snippet_len <= 250, f"Social snippet {snippet_len} not in 150-250 range"
    
    hashtags = content["hashtags"]
    assert isinstance(hashtags, list), "Hashtags must be a list"
    assert 3 <= len(hashtags) <= 10, f"Hashtag count {len(hashtags)} not in 3-10 range"
    
    logger.info(f"✓ Content valid: article {article_len} chars, {len(hashtags)} hashtags")
    return content
