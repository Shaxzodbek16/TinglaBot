from __future__ import annotations
import asyncio
import concurrent.futures
import logging
import os
import time
from pathlib import Path
from typing import Optional
import yt_dlp

from app.bot.extensions.get_random_cookie import get_random_cookie_for_youtube
from app.core.extensions.enums import CookieType
from app.core.extensions.utils import WORKDIR

logger = logging.getLogger(__name__)

# Optimized paths and thread pool
MUSIC_DIR = WORKDIR.parent / "media" / "music"
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

# Much larger thread pool for parallel downloads
_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=min(16, (os.cpu_count() or 1) * 4), thread_name_prefix="yt-dl"
)

# Improved format selection with proper fallbacks
AUDIO_OPTS_SMART = {
    # More robust format selection with better fallbacks
    "format": (
        "bestaudio[ext=m4a]/bestaudio[ext=aac]/bestaudio[ext=mp3]/"
        "bestaudio[acodec=aac]/bestaudio[acodec=mp3]/bestaudio/best"
    ),
    "outtmpl": f"{MUSIC_DIR}/%(title).60s-%(id)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "ignoreerrors": True,
    "socket_timeout": 10,
    "retries": 3,
    "fragment_retries": 3,
    "cookiefile": get_random_cookie_for_youtube(CookieType.YOUTUBE.value),
    # Add extractaudio for audio-only downloads
    "extractaudio": True,
    # Prefer free formats when available
    "prefer_free_formats": True,
}

# Improved video format selection
VIDEO_OPTS = {
    # Better video format selection with size limits and fallbacks
    "format": (
        "bestvideo[height<=720][filesize<45M]+bestaudio[ext=m4a]/best[height<=720][filesize<45M]/"
        "bestvideo[height<=720]+bestaudio/best[height<=720]/best[filesize<45M]/best"
    ),
    "outtmpl": f"{MUSIC_DIR}/%(title).40s-%(id)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "ignoreerrors": True,
    "socket_timeout": 15,
    "retries": 3,
    "fragment_retries": 3,
    "cookiefile": get_random_cookie_for_youtube(CookieType.YOUTUBE.value),
    "merge_output_format": "mp4",  # Ensure consistent output format
}
print("Youtube video handler: ", VIDEO_OPTS["cookiefile"])


def _get_smart_audio_opts(
    convert_to_mp3: bool = False, allow_large: bool = False
) -> dict:
    AUDIO_OPTS_SMART["cookiefile"] = get_random_cookie_for_youtube(
        CookieType.YOUTUBE.value
    )
    opts = AUDIO_OPTS_SMART.copy()

    if allow_large:
        # Remove filesize restrictions for large files
        opts["format"] = (
            "bestaudio[ext=m4a]/bestaudio[ext=aac]/bestaudio[ext=mp3]/"
            "bestaudio[acodec=aac]/bestaudio[acodec=mp3]/bestaudio/best"
        )

    if convert_to_mp3:
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",  # Slightly better quality
            }
        ]
        opts["postprocessor_args"] = [
            "-threads",
            str(min(4, os.cpu_count() or 1)),
            "-loglevel",
            "error",
        ]
        # Remove extractaudio when using postprocessor
        opts.pop("extractaudio", None)

    return opts


def _audio_sync(query: str) -> Optional[str]:
    AUDIO_OPTS_SMART["cookiefile"] = get_random_cookie_for_youtube(
        CookieType.YOUTUBE.value
    )
    """Smart audio download with improved format detection and fallbacks."""
    print("Youtube audio handler: ", AUDIO_OPTS_SMART["cookiefile"])
    try:
        # First attempt: Try to get audio in preferred format
        with yt_dlp.YoutubeDL(_get_smart_audio_opts(False, False)) as ydl:
            try:
                info = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if not info or not info.get("entries") or not info["entries"][0]:
                    logger.warning(f"No search results for: {query}")
                    return None

                # Check available formats before downloading
                entry = info["entries"][0]
                formats = entry.get("formats", [])

                # Log available formats for debugging
                audio_formats = [f for f in formats if f.get("acodec") != "none"]
                logger.info(
                    f"Available audio formats for '{query}': {len(audio_formats)}"
                )

                # Now download with the same options
                info = ydl.extract_info(f"ytsearch1:{query}", download=True)
                entry = info["entries"][0]

            except yt_dlp.utils.DownloadError as e:
                logger.warning(
                    f"First audio download attempt failed for '{query}': {e}"
                )
                # Try with more permissive format selection
                fallback_opts = _get_smart_audio_opts(False, True)
                fallback_opts["format"] = "bestaudio/best"

                with yt_dlp.YoutubeDL(fallback_opts) as fallback_ydl:
                    info = fallback_ydl.extract_info(
                        f"ytsearch1:{query}", download=True
                    )
                    entry = info["entries"][0]

            # Find the downloaded file
            original_path = Path(ydl.prepare_filename(entry))

            # Check for various possible file extensions
            possible_extensions = [".m4a", ".aac", ".mp3", ".webm", ".opus", ".mp4"]
            actual_file = None

            # First check the exact path
            if original_path.exists() and original_path.stat().st_size > 1000:
                actual_file = original_path
            else:
                # Check with different extensions
                for ext in possible_extensions:
                    test_path = original_path.with_suffix(ext)
                    if test_path.exists() and test_path.stat().st_size > 1000:
                        actual_file = test_path
                        break

            if not actual_file:
                logger.warning(f"No audio file found for: {query}")
                return None

            file_ext = actual_file.suffix.lower()

            # If it's already in a good format, return it
            if file_ext in [".m4a", ".mp3", ".aac"]:
                logger.info(f"Downloaded {file_ext} directly: {actual_file.name}")
                return str(actual_file)

            # If it's in a less optimal format, try to convert
            if file_ext in [".webm", ".opus", ".mp4"]:
                logger.info(f"Converting {file_ext} to mp3 for: {query}")

                # Remove the original file
                actual_file.unlink(missing_ok=True)

                # Download again with conversion
                with yt_dlp.YoutubeDL(_get_smart_audio_opts(True, True)) as convert_ydl:
                    info = convert_ydl.extract_info(f"ytsearch1:{query}", download=True)
                    entry = info["entries"][0]

                    mp3_path = Path(convert_ydl.prepare_filename(entry)).with_suffix(
                        ".mp3"
                    )

                    if mp3_path.exists() and mp3_path.stat().st_size > 1000:
                        logger.info(f"Converted to mp3: {mp3_path.name}")
                        return str(mp3_path)

            # If we get here, return the original file even if not ideal
            logger.info(f"Returning {file_ext} file: {actual_file.name}")
            return str(actual_file)

    except Exception as e:
        logger.error(f"Audio download error for '{query}': {e}")

        # Final fallback: try with most basic settings
        try:
            basic_opts = {
                "format": "bestaudio/best",
                "outtmpl": f"{MUSIC_DIR}/%(title).60s-%(id)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "ignoreerrors": True,
                "cookiefile": get_random_cookie_for_youtube(CookieType.YOUTUBE.value),
            }

            with yt_dlp.YoutubeDL(basic_opts) as basic_ydl:
                info = basic_ydl.extract_info(f"ytsearch1:{query}", download=True)
                if info and info.get("entries") and info["entries"][0]:
                    entry = info["entries"][0]
                    file_path = Path(basic_ydl.prepare_filename(entry))

                    # Check for the file with various extensions
                    for ext in [".webm", ".m4a", ".mp3", ".opus", ".mp4"]:
                        test_path = file_path.with_suffix(ext)
                        if test_path.exists() and test_path.stat().st_size > 1000:
                            logger.info(
                                f"Fallback download successful: {test_path.name}"
                            )
                            return str(test_path)

        except Exception as fallback_error:
            logger.error(
                f"Fallback download also failed for '{query}': {fallback_error}"
            )

    return None


def _video_sync(video_id: str, title: str) -> Optional[str]:
    VIDEO_OPTS["cookiefile"] = get_random_cookie_for_youtube(CookieType.YOUTUBE.value)
    """Optimized video download with better error handling and fallbacks."""
    print("Youtube audio handler: ", VIDEO_OPTS["cookiefile"])
    safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:40]

    try:
        # First attempt with optimal settings
        with yt_dlp.YoutubeDL(VIDEO_OPTS) as ydl:
            url = f"https://youtube.com/watch?v={video_id}"

            try:
                ydl.download([url])
            except yt_dlp.utils.DownloadError as e:
                logger.warning(f"Primary video download failed for '{video_id}': {e}")

                # Fallback with simpler format selection
                fallback_opts = VIDEO_OPTS.copy()
                fallback_opts["format"] = "best[filesize<45M]/best"

                with yt_dlp.YoutubeDL(fallback_opts) as fallback_ydl:
                    fallback_ydl.download([url])

            # Check for downloaded file with multiple possible names and extensions
            base_patterns = [
                f"{safe_title}-{video_id}",
                f"*{video_id}*",
                f"{safe_title}*",
            ]

            for pattern in base_patterns:
                for ext in ("mp4", "webm", "mkv", "avi", "flv"):
                    for file_path in MUSIC_DIR.glob(f"{pattern}.{ext}"):
                        if file_path.exists() and file_path.stat().st_size > 1000:
                            logger.info(f"Downloaded video: {file_path.name}")
                            return str(file_path)

    except Exception as e:
        logger.error(f"Video download error for '{video_id}': {e}")

    return None


# Faster async wrappers with improved error handling
async def download_music_from_youtube(title: str, artist: str) -> Optional[str]:
    """Smart music download with format optimization and better error handling."""
    if not title or not artist:
        return None

    query = f"{title} {artist}"
    loop = asyncio.get_running_loop()

    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_pool, _audio_sync, query),
            timeout=60,  # Increased timeout for better reliability
        )
    except asyncio.TimeoutError:
        logger.warning(f"Audio timeout: {title} - {artist}")
        return None
    except Exception as e:
        logger.error(f"Audio error: {e}")
        return None


async def download_video_from_youtube(video_id: str, title: str) -> Optional[str]:
    """Fast video download with improved error handling and fallbacks."""
    if not video_id or not title:
        return None

    loop = asyncio.get_running_loop()

    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_pool, _video_sync, video_id, title),
            timeout=90,  # Increased timeout for video downloads
        )
    except asyncio.TimeoutError:
        logger.warning(f"Video timeout: {video_id}")
        return None
    except Exception as e:
        logger.error(f"Video error: {e}")
        return None


async def cleanup_old_files(max_age: int = 1800) -> None:
    """Enhanced cleanup for all supported formats."""
    if not MUSIC_DIR.exists():
        return

    now = time.time()
    files_to_delete = []

    try:
        # Support all possible audio and video formats
        patterns = [
            "*.m4a",
            "*.mp3",
            "*.aac",
            "*.opus",
            "*.webm",
            "*.mp4",
            "*.mkv",
            "*.avi",
            "*.flv",
            "*.ogg",
            "*.wav",
        ]

        for pattern in patterns:
            for file_path in MUSIC_DIR.glob(pattern):
                if file_path.is_file() and now - file_path.stat().st_mtime > max_age:
                    files_to_delete.append(file_path)

        # Batch delete with better error handling
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                file_path.unlink(missing_ok=True)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Could not delete {file_path.name}: {e}")
                continue

        if deleted_count > 0:
            logger.info(f"Cleaned {deleted_count}/{len(files_to_delete)} files")

    except Exception as e:
        logger.error(f"Cleanup error: {e}")


async def shutdown_downloader() -> None:
    """Graceful shutdown."""
    _pool.shutdown(wait=False)
