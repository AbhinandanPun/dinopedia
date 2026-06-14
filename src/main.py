"""Main entry point for Dinopedia content generation pipeline."""

from src.logger import get_logger
from src.generation.gemini_service import init_gemini
from src.generation.content_generator import generate_dinosaur_content
from src.data.plan import get_pending_dinosaur, mark_complete
from src.data.repository import save_article

logger = get_logger(__name__)

def run_pipeline():
    """Execute single content generation cycle."""
    logger.info("=" * 60)
    logger.info("Dinopedia Pipeline: Starting")
    logger.info("=" * 60)
    
    try:
        # Initialize Gemini
        init_gemini()
        
        # Get next pending dinosaur
        pending = get_pending_dinosaur()
        if not pending:
            logger.info("✓ No pending dinosaurs. Pipeline complete!")
            return
        
        dinosaur_id = pending["id"]
        logger.info(f"\nProcessing: {pending['common_name']} (ID: {dinosaur_id})")
        
        # Generate content
        content = generate_dinosaur_content(dinosaur_id)
        
        # Save to output/
        result = save_article(dinosaur_id, content)
        logger.info(f"✓ Saved to: {result['json']}")
        
        # Mark as complete in plan
        mark_complete(dinosaur_id)
        logger.info(f"✓ Marked complete in plan")
        
        logger.info("\n" + "=" * 60)
        logger.info("Dinopedia Pipeline: SUCCESS")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n✗ Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    run_pipeline()
