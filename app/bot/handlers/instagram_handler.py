from instaloader import Instaloader, Post
from uuid import uuid4
import subprocess
import os
from pathlib import Path

from app.core.extensions.utils import WORKDIR


async def download_instagram_video_only_mp4(url: str) -> str:
    filename = str(uuid4())
    loader = Instaloader(
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern="",
        filename_pattern=filename,
    )

    shortcode = url.strip("/").split("/")[-1]
    post = Post.from_shortcode(loader.context, shortcode)

    target_folder = WORKDIR.parent / "media" / "instagram"
    loader.download_post(post, target=target_folder)

    return str(target_folder / filename) + ".mp4"


def validate_instagram_url(url: str) -> str:
    base_url = url.split("?")[0].strip().rstrip("/")

    parts = base_url.split("/")
    if len(parts) >= 5 and "instagram.com" in parts:
        for i in range(len(parts)):
            if parts[i] in ["reel", "reels"] and i + 1 < len(parts):
                reel_id = parts[i + 1]
                return f"https://www.instagram.com/reel/{reel_id}/"
    return base_url


async def extract_audio_from_instagram_video(url: str) -> str:
    """
    Instagram videosidan audio ajratib olish
    """
    try:
        # Avval videoni yuklab olamiz
        video_path = await download_instagram_video_only_mp4(url)

        if not os.path.exists(video_path):
            raise Exception("Video file not found")

        # Audio fayl uchun nom yaratamiz
        video_name = Path(video_path).stem
        audio_filename = f"{video_name}.mp3"
        audio_path = str(WORKDIR.parent / "media" / "music" / audio_filename)

        # Audio papkasini yaratamiz agar mavjud bo'lmasa
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)

        # FFmpeg bilan audio ajratish
        command = [
            "ffmpeg",
            "-i",
            video_path,
            "-vn",  # Video streamni o'chirish
            "-acodec",
            "mp3",
            "-ab",
            "192k",  # Audio bitrate
            "-ar",
            "44100",  # Sample rate
            "-y",  # Output faylni qayta yozish
            audio_path,
        ]

        # FFmpeg jarayonini ishga tushirish
        process = subprocess.run(command, capture_output=True, text=True, check=True)

        # Video faylni tozalash
        if os.path.exists(video_path):
            os.remove(video_path)

        # Audio fayl yaratilganini tekshirish
        if os.path.exists(audio_path):
            return audio_path
        else:
            raise Exception("Audio file was not created")

    except subprocess.CalledProcessError as e:
        # FFmpeg xatosi
        error_msg = e.stderr if e.stderr else "FFmpeg process failed"
        raise Exception(f"FFmpeg error: {error_msg}")
    except Exception as e:
        raise Exception(f"Audio extraction failed: {str(e)}")


async def extract_audio_with_moviepy(url: str) -> str:
    """
    MoviePy kutubxonasi bilan audio ajratish (FFmpeg alternativasi)
    """
    try:
        from moviepy.editor import VideoFileClip

        # Video yuklab olish
        video_path = await download_instagram_video_only_mp4(url)

        if not os.path.exists(video_path):
            raise Exception("Video file not found")

        # Audio fayl nomi
        video_name = Path(video_path).stem
        audio_filename = f"{video_name}.mp3"
        audio_path = str(WORKDIR.parent / "media" / "music" / audio_filename)

        # Audio papkasini yaratish
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)

        # Video yuklab olish va audio ajratish
        video = VideoFileClip(video_path)
        audio = video.audio

        # Audio faylni saqlash
        audio.write_audiofile(
            audio_path, verbose=False, logger=None, codec="mp3", bitrate="192k"
        )

        # Resurslarni tozalash
        audio.close()
        video.close()

        # Video faylni o'chirish
        if os.path.exists(video_path):
            os.remove(video_path)

        return audio_path

    except ImportError:
        raise Exception(
            "MoviePy library is not installed. Please install: pip install moviepy"
        )
    except Exception as e:
        raise Exception(f"Audio extraction with MoviePy failed: {str(e)}")


def check_ffmpeg_installed() -> bool:
    """
    FFmpeg o'rnatilganligini tekshirish
    """
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


async def extract_audio_from_instagram_video_smart(url: str) -> str:
    """
    Aqlli audio ajratish: avval FFmpeg, keyin MoviePy
    """
    if check_ffmpeg_installed():
        try:
            return await extract_audio_from_instagram_video(url)
        except Exception:
            # FFmpeg ishlamasa, MoviePy ishlatamiz
            return await extract_audio_with_moviepy(url)
    else:
        # FFmpeg yo'q bo'lsa MoviePy ishlatamiz
        return await extract_audio_with_moviepy(url)
