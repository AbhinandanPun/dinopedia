import os
from dotenv import load_dotenv

load_dotenv()

def get_api_key():
    """Get Gemini API key from environment."""
    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError("GOOGLE_API_KEY not set in .env")
    return key
