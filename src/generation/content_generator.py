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
    
    # Validate field lengths and fix them gracefully
    article_len = len(content["article"])
    if not (3000 <= article_len <= 10000):
        logger.warning(f"Article length {article_len} is outside expected range (3000-10000).")
    
    snippet_len = len(content["social_snippet"])
    if snippet_len > 250:
        logger.warning(f"Social snippet too long ({snippet_len} chars). Truncating to 250.")
        content["social_snippet"] = content["social_snippet"][:247] + "..."
    elif snippet_len < 100:
        logger.warning(f"Social snippet might be too short ({snippet_len} chars).")
        
    hashtags = content["hashtags"]
    if not isinstance(hashtags, list):
        logger.warning("Hashtags is not a list, attempting to parse...")
        if isinstance(hashtags, str):
            content["hashtags"] = [h.strip() for h in hashtags.split()]
        else:
            content["hashtags"] = ["#Dinosaurs"]
            
    if len(content["hashtags"]) > 10:
        logger.warning(f"Too many hashtags ({len(content['hashtags'])}). Limiting to 10.")
        content["hashtags"] = content["hashtags"][:10]
        
    logger.info(f"✓ Content ready: article {article_len} chars, {len(content['hashtags'])} hashtags")
    return content
