"""Slide generation using PIL."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from src.media.image_fetcher import get_pexels_image
from src.logger import get_logger
from src.utils.file_io import ensure_directory

logger = get_logger(__name__)

ASSETS_PATH = Path("assets")
FONT_FILE = ASSETS_PATH / "fonts" / "arial.ttf"
FALLBACK_FONT = ImageFont.load_default()
BRAND_NAME = "Dinopedia 🦕"

def generate_visuals(output_dir, video_type, slide_content=None, thumbnail_title=None, slide_number=0, total_slides=0):
    """
    Generate a single professional slide or thumbnail.
    """
    output_dir = Path(output_dir)
    ensure_directory(output_dir)
    is_thumbnail = thumbnail_title is not None

    width, height = (1920, 1080) if video_type == 'long' else (1080, 1920)
    title = thumbnail_title if is_thumbnail else slide_content.get("title", "")
    bg_image = get_pexels_image(title, video_type)

    if not bg_image:
        bg_image = Image.new('RGBA', (width, height), color=(20, 30, 20))
    
    bg_image = bg_image.resize((width, height)).filter(ImageFilter.GaussianBlur(5))
    darken_layer = Image.new('RGBA', bg_image.size, (0, 0, 0, 150))
    final_bg = Image.alpha_composite(bg_image, darken_layer).convert("RGB")

    if is_thumbnail and video_type == 'long':
        w, h = final_bg.size
        if h > w:
            logger.info("Detected vertical thumbnail for long video. Rotating and resizing...")
            final_bg = final_bg.transpose(Image.ROTATE_270).resize((1920, 1080))

    draw = ImageDraw.Draw(final_bg)

    try:
        title_font = ImageFont.truetype(str(FONT_FILE), 80 if video_type == 'long' else 90)
        content_font = ImageFont.truetype(str(FONT_FILE), 45 if video_type == 'long' else 55)
        footer_font = ImageFont.truetype(str(FONT_FILE), 25 if video_type == 'long' else 35)
    except IOError:
        logger.warning(f"Font file {FONT_FILE} not found. Using fallback.")
        title_font = content_font = footer_font = FALLBACK_FONT

    if not is_thumbnail:
        # Header background
        header_height = int(height * 0.18)
        draw.rectangle([0, 0, width, header_height], fill=(30, 50, 40, 200))

        # Wrap title text
        words = title.split()
        title_lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = draw.textbbox((0, 0), test_line, font=title_font)
            if bbox[2] - bbox[0] < width * 0.9:
                current_line = test_line
            else:
                title_lines.append(current_line)
                current_line = word
        title_lines.append(current_line)

        line_height = title_font.getbbox("A")[3] + 10
        total_title_height = len(title_lines) * line_height
        y_text = (header_height - total_title_height) / 2

        for line in title_lines:
            bbox = draw.textbbox((0, 0), line, font=title_font)
            x = (width - (bbox[2] - bbox[0])) / 2
            draw.text((x, y_text), line, font=title_font, fill=(255, 255, 255))
            y_text += line_height
    else:
        # Center title on thumbnail
        bbox = draw.textbbox((0, 0), title, font=title_font)
        x = (width - (bbox[2] - bbox[0])) / 2
        y = (height - (bbox[3] - bbox[1])) / 2
        draw.text((x, y), title, font=title_font, fill=(255, 255, 255), stroke_width=2, stroke_fill="black")

    if not is_thumbnail:
        # Main content block
        content = slide_content.get("content", "")
        is_special_slide = len(content.split()) < 10

        words = content.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if draw.textbbox((0, 0), test_line, font=content_font)[2] < width * 0.85:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        line_height = content_font.getbbox("A")[3] + 15
        total_text_height = len(lines) * line_height
        y_text = (height - total_text_height) / 2 if is_special_slide else header_height + 100

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=content_font)
            x = (width - (bbox[2] - bbox[0])) / 2
            draw.text((x, y_text), line, font=content_font, fill=(230, 230, 230))
            y_text += line_height

        # Footer
        footer_height = int(height * 0.06)
        draw.rectangle([0, height - footer_height, width, height], fill=(30, 50, 40, 200))
        draw.text((40, height - footer_height + 12), BRAND_NAME, font=footer_font, fill=(180, 180, 180))

        if total_slides > 0:
            slide_num_text = f"Slide {slide_number} of {total_slides}"
            bbox = draw.textbbox((0, 0), slide_num_text, font=footer_font)
            draw.text((width - bbox[2] - 40, height - footer_height + 12), slide_num_text, font=footer_font, fill=(180, 180, 180))

    file_prefix = "thumbnail" if is_thumbnail else f"slide_{slide_number:02d}"
    path = output_dir / f"{file_prefix}.png"
    final_bg.save(path)
    logger.info(f"Generated visual: {path}")
    return str(path)
