"""YouTube uploader module."""

import os
import base64
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from src.logger import get_logger

logger = get_logger(__name__)

CLIENT_SECRETS_FILE = Path('client_secrets.json')
CREDENTIALS_FILE = Path('credentials.json')
YOUTUBE_UPLOAD_SCOPE = ["https://www.googleapis.com/auth/youtube.upload"]

def _decode_b64_to_file(b64_env_var, output_path):
    """Decode base64 env var to file."""
    b64_data = os.getenv(b64_env_var)
    if b64_data:
        try:
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(b64_data))
            logger.info(f"Decoded {b64_env_var} to {output_path}")
        except Exception as e:
            logger.error(f"Failed to decode {b64_env_var}: {e}")

def get_authenticated_service():
    """Handles OAuth2 flow and returns authenticated YouTube service."""
    if not CREDENTIALS_FILE.exists():
        _decode_b64_to_file("CREDENTIALS_B64", CREDENTIALS_FILE)
    if not CLIENT_SECRETS_FILE.exists():
        _decode_b64_to_file("CLIENT_SECRET_B64", CLIENT_SECRETS_FILE)

    credentials = None
    if CREDENTIALS_FILE.exists():
        logger.info("Found credentials.json")
        credentials = Credentials.from_authorized_user_file(str(CREDENTIALS_FILE), YOUTUBE_UPLOAD_SCOPE)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            logger.info("Refreshing expired credentials...")
            credentials.refresh(Request())
        else:
            logger.info("No valid credentials found. Starting new authentication flow...")
            if not CLIENT_SECRETS_FILE.exists():
                raise FileNotFoundError(f"CRITICAL ERROR: {CLIENT_SECRETS_FILE} not found.")
            
            flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS_FILE), scopes=YOUTUBE_UPLOAD_SCOPE)
            credentials = flow.run_local_server(port=0)
        
        with open(CREDENTIALS_FILE, 'w') as f:
            f.write(credentials.to_json())
            
    return build('youtube', 'v3', credentials=credentials)

def upload_to_youtube(video_path, title, description, tags, thumbnail_path=None):
    """Upload video to YouTube."""
    logger.info(f"⬆️ Uploading '{video_path}' to YouTube...")
    try:
        youtube = get_authenticated_service()
        
        request_body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags.split(','),
                'categoryId': '27' # Education
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False
            }
        }

        media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
        
        request = youtube.videos().insert(
            part=','.join(request_body.keys()),
            body=request_body,
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}%.")
                
        video_id = response.get('id')
        logger.info(f"✅ Video uploaded! ID: {video_id}")

        if thumbnail_path and os.path.exists(thumbnail_path):
            logger.info(f"⬆️ Uploading thumbnail...")
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path))
                ).execute()
                logger.info("✅ Thumbnail uploaded!")
            except Exception as e:
                logger.error(f"❌ Failed to upload thumbnail: {e}")

        return video_id
        
    except Exception as e:
        logger.error(f"❌ Failed to upload to YouTube: {e}")
        raise
