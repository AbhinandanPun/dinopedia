"""Video rendering using MoviePy."""

from pathlib import Path
from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_videoclips, vfx
from src.logger import get_logger
from src.utils.file_io import ensure_directory

logger = get_logger(__name__)

ASSETS_PATH = Path("assets")
BACKGROUND_MUSIC_PATH = ASSETS_PATH / "music" / "bg_music.mp3"

def create_video(slide_paths, audio_paths, output_path, video_type):
    """
    Assemble slides and audio into a final video.
    """
    output_path = Path(output_path)
    ensure_directory(output_path.parent)
    logger.info(f"[VIDEO] Creating {video_type} video: {output_path.name}...")
    
    try:
        if not slide_paths or not audio_paths or len(slide_paths) != len(audio_paths):
            raise ValueError("Mismatch between slides and audio clips, or no slides provided.")

        image_clips = []
        for i, (img_path, audio_path) in enumerate(zip(slide_paths, audio_paths)):
            audio_clip = AudioFileClip(str(audio_path))
            duration = audio_clip.duration + 0.5  # Padding
            img_clip = (
                ImageClip(str(img_path))
                .set_duration(duration)
                .set_audio(audio_clip)
                .fadein(0.5)
                .fadeout(0.5)
            )
            image_clips.append(img_clip)

        final_video = concatenate_videoclips(image_clips, method="compose")

        if BACKGROUND_MUSIC_PATH.exists():
            logger.info("[MUSIC] Adding background music...")
            bg_music = AudioFileClip(str(BACKGROUND_MUSIC_PATH)).volumex(0.05)
            if bg_music.duration < final_video.duration:
                bg_music = bg_music.fx(vfx.loop, duration=final_video.duration)
            else:
                bg_music = bg_music.subclip(0, final_video.duration)

            composite_audio = CompositeAudioClip([
                final_video.audio.volumex(1.2),
                bg_music
            ])
            final_video = final_video.set_audio(composite_audio)

        final_video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            audio_bitrate="192k",
            preset="ultrafast",
            threads=4
        )
        
        # Explicitly close MoviePy clips to prevent [WinError 6] during garbage collection
        final_video.close()
        if 'composite_audio' in locals():
            composite_audio.close()
        if 'bg_music' in locals():
            bg_music.close()
        for clip in image_clips:
            if hasattr(clip, 'audio') and clip.audio:
                clip.audio.close()
            clip.close()
            
        logger.info(f"✅ Video created successfully: {output_path}")

    except Exception as e:
        logger.error(f"❌ ERROR during video creation: {e}")
        raise
