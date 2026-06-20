"""Tests for slide generation."""

import pytest
from unittest.mock import patch, MagicMock
from src.media.slide_generator import generate_visuals

@patch('src.media.slide_generator.get_pexels_image')
@patch('src.media.slide_generator.Image.new')
def test_generate_visuals_slide(mock_image_new, mock_get_pexels, tmp_path):
    mock_get_pexels.return_value = None
    mock_bg = MagicMock()
    mock_image_new.return_value = mock_bg
    mock_bg.resize().filter().size = (1920, 1080)
    
    slide_content = {"title": "Test Slide", "content": "This is test content."}
    
    with patch('src.media.slide_generator.Image.alpha_composite') as mock_composite:
        mock_final = MagicMock()
        mock_composite.return_value.convert.return_value = mock_final
        
        with patch('src.media.slide_generator.ImageDraw.Draw') as mock_draw_cls:
            mock_draw = MagicMock()
            mock_draw.textbbox.return_value = (0.0, 0.0, 100.0, 20.0)
            mock_draw_cls.return_value = mock_draw
            
            result = generate_visuals(tmp_path, "long", slide_content=slide_content, slide_number=1, total_slides=1)
            
            assert "slide_01.png" in result
            mock_final.save.assert_called_once()
