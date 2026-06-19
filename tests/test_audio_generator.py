"""Tests for audio generation."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.media.audio_generator import text_to_speech, generate_slide_audio

@patch('src.media.audio_generator.gTTS')
@patch('src.media.audio_generator.AudioSegment')
@patch('src.media.audio_generator.os.remove')
def test_text_to_speech(mock_remove, mock_audio_segment, mock_gtts, tmp_path):
    output_path = tmp_path / "test.wav"
    
    mock_audio = MagicMock()
    mock_audio_segment.from_mp3.return_value = mock_audio
    
    result = text_to_speech("Hello", output_path)
    
    assert result == output_path
    mock_gtts.assert_called_once_with(text="Hello", lang='en', slow=False)
    mock_audio.export.assert_called_once_with(str(output_path), format="wav", codec="pcm_s16le")

@patch('src.media.audio_generator.text_to_speech')
def test_generate_slide_audio(mock_tts, tmp_path):
    mock_tts.return_value = tmp_path / "slide_00.wav"
    
    slides = [{"title": "Title", "content": "Content"}]
    result = generate_slide_audio(slides, tmp_path)
    
    assert len(result) == 1
    mock_tts.assert_called_once()
