from __future__ import annotations
import asyncio
import concurrent.futures
import logging
import os
import time
from pathlib import Path
from typing import Optional
import yt_dlp
from app.core.extensions.utils import WORKDIR

logger = logging.getLogger(__name__)

# Optimized paths and thread pool
MUSIC_DIR = WORKDIR.parent / "media" / "music"
MUSIC_DIR.mkdir(parents=True, exist_ok=True)

# Much larger thread pool for parallel downloads
_pool = concurrent.futures.ThreadPoolExecutor(
    max_workers=min(16, (os.cpu_count() or 1) * 4), thread_name_prefix="yt-dl"
)

# Smart format selection - try best formats first
AUDIO_OPTS_SMART = {
    "format": (
        "bestaudio[ext=m4a][filesize<50M]/"
        "bestaudio[ext=aac][filesize<50M]/"
        "bestaudio[acodec=aac][filesize<50M]/"
        "bestaudio[filesize<50M]/"
        "best[filesize<50M]/best"
    ),
    "outtmpl": f"{MUSIC_DIR}/%(title).60s-%(id)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "ignoreerrors": True,
    "socket_timeout": 10,
    "retries": 2,
    "fragment_retries": 2,
    "cookiefile": WORKDIR.parent / "static" / "cookie" / "youtube.txt",
    # Dynamic postprocessor - only convert if not m4a/mp3
}

VIDEO_OPTS = {
    "format": "best[height<=720][filesize<45M]/best[filesize<45M]/best",
    "outtmpl": f"{MUSIC_DIR}/%(title).40s-%(id)s.%(ext)s",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "ignoreerrors": True,
    "socket_timeout": 15,
    "retries": 2,
    "cookiefile": WORKDIR.parent / "static" / "cookie" / "youtube.txt",
}


def _get_smart_audio_opts(
    convert_to_mp3: bool = False, allow_large: bool = False
) -> dict:
    opts = AUDIO_OPTS_SMART.copy()

    if allow_large:
        opts["format"] = (
            "bestaudio[ext=m4a]/" "bestaudio[acodec=aac]/" "bestaudio/" "best"
        )

    if convert_to_mp3:
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ]
        opts["postprocessor_args"] = ["-threads", "4", "-loglevel", "error"]

    return opts


def _audio_sync(query: str) -> Optional[str]:
    """Smart audio download with format detection."""
    try:
        # First attempt: Try to get best audio format without conversion
        with yt_dlp.YoutubeDL(_get_smart_audio_opts(False, False)) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)

            if not info or not info.get("entries") or not info["entries"][0]:
                return None

            entry = info["entries"][0]
            original_path = Path(ydl.prepare_filename(entry))

            # Check what format was actually downloaded
            actual_file = None
            for possible_path in [original_path] + [
                original_path.with_suffix(ext)
                for ext in [".m4a", ".webm", ".opus", ".mp4", ".aac"]
            ]:
                if possible_path.exists() and possible_path.stat().st_size > 1000:
                    actual_file = possible_path
                    break

            if not actual_file:
                logger.warning(f"No audio file found for: {query}")
                return None

            file_ext = actual_file.suffix.lower()

            # If it's already m4a or mp3, return directly
            if file_ext in [".m4a", ".mp3", ".aac"]:
                logger.info(f"Downloaded {file_ext} directly: {actual_file.name}")
                return str(actual_file)

            # If it's other format, convert to mp3
            logger.info(f"Converting {file_ext} to mp3 for: {query}")

            # Remove the downloaded file and try again with conversion
            actual_file.unlink(missing_ok=True)

        # Second attempt: Convert to mp3
        with yt_dlp.YoutubeDL(_get_smart_audio_opts(True, True)) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)

            if not info or not info.get("entries") or not info["entries"][0]:
                return None

            entry = info["entries"][0]
            mp3_path = Path(ydl.prepare_filename(entry)).with_suffix(".mp3")

            if mp3_path.exists() and mp3_path.stat().st_size > 1000:
                logger.info(f"Converted to mp3: {mp3_path.name}")
                return str(mp3_path)

    except Exception as e:
        logger.error(f"Audio download error for '{query}': {e}")

    return None


def _video_sync(video_id: str, title: str) -> Optional[str]:
    """Optimized video download with better error handling."""
    safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[:40]

    try:
        with yt_dlp.YoutubeDL(VIDEO_OPTS) as ydl:
            url = f"https://youtube.com/watch?v={video_id}"
            ydl.download([url])

            # Check for downloaded file with multiple possible names
            base_patterns = [
                f"{safe_title}-{video_id}",
                f"*{video_id}*",
                f"{safe_title}*",
            ]

            for pattern in base_patterns:
                for ext in ("mp4", "webm", "mkv", "avi"):
                    for file_path in MUSIC_DIR.glob(f"{pattern}.{ext}"):
                        if file_path.exists() and file_path.stat().st_size > 1000:
                            logger.info(f"Downloaded video: {file_path.name}")
                            return str(file_path)

    except Exception as e:
        logger.error(f"Video download error for '{video_id}': {e}")

    return None


# Faster async wrappers
async def download_music_from_youtube(title: str, artist: str) -> Optional[str]:
    """Smart music download with format optimization."""
    if not title or not artist:
        return None

    query = f"{title} {artist}"
    loop = asyncio.get_running_loop()

    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_pool, _audio_sync, query),
            timeout=40,  # Balanced timeout for both scenarios
        )
    except asyncio.TimeoutError:
        logger.warning(f"Audio timeout: {title} - {artist}")
        return None
    except Exception as e:
        logger.error(f"Audio error: {e}")
        return None


async def download_video_from_youtube(video_id: str, title: str) -> Optional[str]:
    """Fast video download with improved error handling."""
    if not video_id or not title:
        return None

    loop = asyncio.get_running_loop()

    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_pool, _video_sync, video_id, title), timeout=60
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
