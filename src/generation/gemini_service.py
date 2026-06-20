"""Wrapper around Google Gemini API."""

import json
import google.genai as genai
from src.config import get_api_key
from src.logger import get_logger

logger = get_logger(__name__)
_client = None

def init_gemini():
    """Initialize Gemini client with API key."""
    global _client
    api_key = get_api_key()
    _client = genai.Client(api_key=api_key)
    logger.info("Gemini client initialized")

def generate_content(prompt, model="gemini-2.5-flash"):
    """Generate content from prompt using Gemini."""
    try:
        if _client is None:
            raise RuntimeError("Gemini not initialized. Call init_gemini() first.")
        
        response = _client.models.generate_content(
            model=model,
            contents=prompt
        )
        text = response.text
        logger.info(f"Generated content with {model}, tokens used: ~{len(text.split())}")
        return text
    except Exception as e:
        logger.error(f"Gemini generation failed: {e}")
        raise

def generate_dinosaur_article(dinosaur, model="gemini-2.5-flash"):
    """Generate and parse dinosaur article content."""
    from src.generation.prompts import get_article_prompt
    
    prompt = get_article_prompt(dinosaur)
    logger.info(f"Generating article for {dinosaur['common_name']}")
    
    response_text = generate_content(prompt, model)
    
    # Parse JSON response
    try:
        # Strip markdown formatting if present
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        
        content = json.loads(clean_text)
        logger.info(f"Successfully generated article ({len(content['article'])} chars)")
        return content
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.debug(f"Raw response: {response_text[:200]}")
        raise
