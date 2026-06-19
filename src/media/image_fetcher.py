"""Image fetching utility for Pexels API."""

import os
from io import BytesIO
import requests
from PIL import Image
from src.logger import get_logger

logger = get_logger(__name__)

def get_pexels_image(query, video_type):
    """
    Search for a relevant image on Pexels.
    
    Args:
        query (str): Search query
        video_type (str): 'long' (landscape) or 'short' (portrait)
        
    Returns:
        Image object or None if failed/no key
    """
    pexels_api_key = os.getenv("PEXELS_API_KEY")
    if not pexels_api_key:
        logger.warning("PEXELS_API_KEY not found. Using solid color background.")
        return None

    orientation = 'landscape' if video_type == 'long' else 'portrait'
    try:
        headers = {"Authorization": pexels_api_key}
        params = {"query": f"dinosaur {query} abstract", "per_page": 1, "orientation": orientation}
        response = requests.get("https://api.pexels.com/v1/search", headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get('photos'):
            image_url = data['photos'][0]['src']['large2x']
            image_response = requests.get(image_url, timeout=15)
            image_response.raise_for_status()
            return Image.open(BytesIO(image_response.content)).convert("RGBA")
            
        logger.warning(f"No Pexels images found for query: {query}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching Pexels image for query '{query}': {e}")
    except Exception as e:
        logger.error(f"General error fetching Pexels image for query '{query}': {e}")
        
    return None
