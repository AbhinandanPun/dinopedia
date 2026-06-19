"""Audio generation module using gTTS."""

import os
from pathlib import Path
from gtts import gTTS
from pydub import AudioSegment
from src.logger import get_logger
from src.utils.file_io import ensure_directory

logger = get_logger(__name__)

def text_to_speech(text, output_path):
    """
    Convert text to speech using gTTS and save as WAV.
    
    Args:
        text (str): Text to convert
        output_path (Path or str): Output file path (.wav)
        
    Returns:
        Path: Path to generated WAV file
    """
    output_path = Path(output_path)
    ensure_directory(output_path.parent)
    logger.info(f"🎤 Converting text to speech: {output_path.name}")
    
    try:
        temp_mp3_path = str(output_path).replace('.wav', '_temp.mp3')
        wav_path = str(output_path.with_suffix('.wav'))

        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(temp_mp3_path)

        audio = AudioSegment.from_mp3(temp_mp3_path)
        audio.export(wav_path, format="wav", codec="pcm_s16le")
        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)

        logger.info(f"✅ Speech generated and converted to WAV successfully!")
        return Path(wav_path)

    except Exception as e:
        logger.error(f"❌ ERROR: Failed to generate speech: {e}")
        raise

def generate_slide_audio(slides, output_dir):
    """
    Generate audio for a list of slides.
    
    Args:
        slides (list): List of slide dicts (must have 'title' and 'content')
        output_dir (Path or str): Directory to save audio files
        
    Returns:
        list: List of Path objects to generated audio files
    """
    output_dir = Path(output_dir)
    ensure_directory(output_dir)
    
    audio_paths = []
    for i, slide in enumerate(slides):
        text = f"{slide['title']}. {slide['content']}"
        output_path = output_dir / f"slide_{i:02d}.wav"
        audio_path = text_to_speech(text, output_path)
        audio_paths.append(audio_path)
        
    return audio_paths

def generate_short_audio(highlight_text, output_dir):
    """
    Generate single audio track for YouTube Shorts.
    
    Args:
        highlight_text (str): Short highlight text
        output_dir (Path or str): Directory to save audio
        
    Returns:
        Path: Path to generated audio file
    """
    output_dir = Path(output_dir)
    ensure_directory(output_dir)
    output_path = output_dir / "short_highlight.wav"
    return text_to_speech(highlight_text, output_path)
