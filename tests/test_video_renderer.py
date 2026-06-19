"""Tests for video rendering."""

import pytest
from unittest.mock import patch, MagicMock
from src.media.video_renderer import create_video

@patch('src.media.video_renderer.AudioFileClip')
@patch('src.media.video_renderer.ImageClip')
@patch('src.media.video_renderer.concatenate_videoclips')
def test_create_video(mock_concat, mock_img_clip, mock_audio_clip, tmp_path):
    mock_audio = MagicMock()
    mock_audio.duration = 2.0
    mock_audio_clip.return_value = mock_audio
    
    mock_img = MagicMock()
    mock_img.set_duration.return_value = mock_img
    mock_img.set_audio.return_value = mock_img
    mock_img.fadein.return_value = mock_img
    mock_img.fadeout.return_value = mock_img
    mock_img_clip.return_value = mock_img
    
    mock_final = MagicMock()
    mock_concat.return_value = mock_final
    
    out_path = tmp_path / "out.mp4"
    
    with patch('src.media.video_renderer.BACKGROUND_MUSIC_PATH.exists', return_value=False):
        create_video(["slide1.png"], ["audio1.wav"], out_path, "long")
        
        mock_final.write_videofile.assert_called_once()
