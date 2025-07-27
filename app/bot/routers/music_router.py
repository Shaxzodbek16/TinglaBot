from __future__ import annotations
import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.bot.controller.shazam_controller import ShazamController
from app.bot.extensions.clear import atomic_clear
from app.bot.handlers import shazam_handler as shz
from app.bot.handlers.statistics_handler import update_statistics
from app.bot.handlers.user_handlers import remove_token
from app.bot.keyboards.payment_keyboard import get_payment_keyboard

logger = logging.getLogger(__name__)

music_router = Router()
PAGE, COOLDOWN = 10, 5

# Global state with better management
_controller: Optional[ShazamController] = None
_cache: Dict[int, Dict] = {}
_download_queue: Dict[int, float] = {}
_cleanup_task: Optional[asyncio.Task] = None

# Cache cleanup settings
CACHE_CLEANUP_INTERVAL = 1800  # 30 minutes
CACHE_MAX_AGE = 600  # 10 minutes


def get_controller() -> ShazamController:
    """Singleton controller with lazy initialization."""
    global _controller
    if _controller is None:
        _controller = ShazamController()
        # Start cleanup task when controller is first created
        _start_cleanup_task()
    return _controller


def _start_cleanup_task():
    """Start cleanup task only when event loop is available."""
    global _cleanup_task
    try:
        if _cleanup_task is None or _cleanup_task.done():
            _cleanup_task = asyncio.create_task(cleanup_cache_loop())
    except RuntimeError:
        # Event loop not running yet, task will be started later
        logger.debug("Event loop not running, cleanup task will start later")


# ── helpers with improvements ─────────────────────────────────────────────────
def create_keyboard(
    user_id: int, page: int, add_video: bool = False
) -> InlineKeyboardMarkup:
    """Create paginated keyboard with video option."""
    if user_id not in _cache:
        return InlineKeyboardMarkup(inline_keyboard=[])

    hits = _cache[user_id]["hits"]
    start, end = page * PAGE, (page + 1) * PAGE

    # Create number buttons (5 per row)
    rows = []
    current_row = []

    for offset, index in enumerate(range(start, min(end, len(hits))), 1):
        current_row.append(
            InlineKeyboardButton(
                text=str(index + 1), callback_data=f"music:sel:{index}"
            )
        )
        if offset % 5 == 0:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    # Navigation buttons
    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"music:page:{page - 1}")
        )
    if end < len(hits):
        nav_row.append(
            InlineKeyboardButton(text="➡️", callback_data=f"music:page:{page + 1}")
        )

    if nav_row:
        rows.append(nav_row)

    # Video button for media recognition
    if add_video and hits:
        rows.append(
            [InlineKeyboardButton(text="🎬 Video (top)", callback_data="music:video:0")]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def format_page_text(hits: List[Dict], page: int) -> str:
    """Format page text with better error handling."""
    if not hits:
        return "No results found."

    start_idx, end_idx = page * PAGE, (page + 1) * PAGE
    lines = [f"<b>🎵 Results — Page {page + 1}</b>\n"]

    for number, hit in enumerate(hits[start_idx:end_idx], start=start_idx + 1):
        try:
            title = hit.get("title", "Unknown")[:50]
            artist = hit.get("artist", "Unknown")[:30]
            duration = hit.get("duration", 0)

            # Format duration
            if duration and duration > 0:
                minutes, seconds = divmod(int(duration), 60)
                duration_str = f" ({minutes}:{seconds:02d})"
            else:
                duration_str = ""

            lines.append(f"{number}. <b>{title}</b> — {artist}{duration_str}")

        except Exception as e:
            logger.error(f"Error formatting hit {number}: {e}")
            lines.append(f"{number}. Error formatting result")

    return "\n".join(lines)


def is_cache_valid(user_id: int) -> bool:
    """Check if user cache is valid."""
    if user_id not in _cache:
        return False

    cache_age = time.time() - _cache[user_id]["timestamp"]
    return cache_age < CACHE_MAX_AGE


def can_download(user_id: int) -> bool:
    """Check if user can download (rate limiting)."""
    last_download = _download_queue.get(user_id, 0)
    return time.time() - last_download >= COOLDOWN


# ── telegram file download helper ─────────────────────────────────────────────
async def download_telegram_file(message: Message) -> Optional[str]:
    """Download telegram media file with error handling."""
    try:
        media = message.voice or message.audio or message.video or message.video_note
        if not media:
            return None

        file_info = await message.bot.get_file(media.file_id)
        if not file_info.file_path:
            return None

        # Create temporary file
        temp_path = shz.MUSIC_DIR / f"{uuid4()}_temp"
        await message.bot.download_file(file_info.file_path, destination=temp_path)

        # Verify download
        if temp_path.exists() and temp_path.stat().st_size > 0:
            return str(temp_path)

    except Exception as e:
        logger.error(f"Error downloading Telegram file: {e}")

    return None


# ── cache cleanup task ────────────────────────────────────────────────────────
async def cleanup_cache_loop():
    """Periodic cache cleanup."""
    while True:
        try:
            await asyncio.sleep(CACHE_CLEANUP_INTERVAL)
            current_time = time.time()

            # Clean expired cache entries
            expired_users = [
                user_id
                for user_id, data in _cache.items()
                if current_time - data["timestamp"] > CACHE_MAX_AGE
            ]

            for user_id in expired_users:
                del _cache[user_id]

            # Clean old download queue entries
            expired_downloads = [
                user_id
                for user_id, timestamp in _download_queue.items()
                if current_time - timestamp > COOLDOWN * 10
            ]

            for user_id in expired_downloads:
                del _download_queue[user_id]

            if expired_users or expired_downloads:
                logger.info(
                    f"Cleaned cache: {len(expired_users)} users, {len(expired_downloads)} downloads"
                )

        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")


# ── message handlers ──────────────────────────────────────────────────────────
@music_router.message(F.text)
async def handle_text_query(message: Message):
    """Handle text search queries."""
    # Ensure cleanup task is running
    res = await remove_token(message)
    if not res:
        await message.answer("You have no any requests left.", reply_markup=get_payment_keyboard())
        return

    _start_cleanup_task()

    query = message.text.strip() if message.text else ""

    if len(query) < 2:
        await message.answer("⚠️ Please enter at least 2 characters to search.")
        return

    # Limit query length
    if len(query) > 100:
        query = query[:100]

    status_message = await message.answer("🔍 Searching...")

    try:
        hits = await get_controller().search(query)

        if not hits:
            await status_message.edit_text(
                "😕 No results found. Try different keywords."
            )
            return

        # Cache results
        _cache[message.from_user.id] = {"hits": hits, "timestamp": time.time()}

        await status_message.edit_text(
            format_page_text(hits, 0),
            reply_markup=create_keyboard(message.from_user.id, 0),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"Text search error: {e}")
        await status_message.edit_text("❌ Search failed. Please try again.")
    await update_statistics(message.from_user.id, field="from_text")


@music_router.message(F.voice | F.audio | F.video | F.video_note)
async def handle_media_query(message: Message):
    """Handle media recognition queries."""
    # Ensure cleanup task is running
    _start_cleanup_task()

    status_message = await message.answer("🔍 Analyzing audio...")

    try:
        # Download telegram file
        temp_path = await download_telegram_file(message)
        if not temp_path:
            await status_message.edit_text("❌ Could not download media file.")
            return

        try:
            # Recognize music
            shazam_hits = await shz.recognise_music_from_audio(temp_path)

            if not shazam_hits:
                await status_message.edit_text(
                    "😕 Could not recognize any music in this file."
                )
                return

            # Get best match and search YouTube
            best_track = shazam_hits[0]["track"]
            search_query = f"{best_track['title']} {best_track['subtitle']}"

            youtube_hits = await get_controller().search(search_query)

            if not youtube_hits:
                # Fallback to Shazam data
                youtube_hits = [
                    get_controller().ytdict_to_info(
                        {
                            "title": best_track["title"],
                            "artist": best_track["subtitle"],
                            "duration": 0,
                            "id": best_track.get("key", ""),
                        }
                    )
                ]

            # Cache results
            _cache[message.from_user.id] = {
                "hits": youtube_hits,
                "timestamp": time.time(),
            }

            await status_message.edit_text(
                format_page_text(youtube_hits, 0),
                reply_markup=create_keyboard(message.from_user.id, 0, add_video=True),
                parse_mode="HTML",
            )

        finally:
            # Always cleanup temp file
            if temp_path and Path(temp_path).exists():
                Path(temp_path).unlink(missing_ok=True)

    except Exception as e:
        logger.error(f"Media recognition error: {e}")
        await status_message.edit_text("❌ Recognition failed. Please try again.")
    if message.video:
        await update_statistics(message.from_user.id, field="from_video")
    if message.voice or message.audio:
        await update_statistics(message.from_user.id, field="from_voice")


# ── callback handlers ─────────────────────────────────────────────────────────
@music_router.callback_query(F.data.startswith("music:"))
async def handle_callbacks(callback: CallbackQuery):
    """Handle callback queries with better error handling."""
    await callback.answer()

    try:
        parts = callback.data.split(":")[1:]
        action = parts[0]
        user_id = callback.from_user.id

        if action == "page":
            page = int(parts[1])
            if not is_cache_valid(user_id):
                await callback.message.answer(
                    "⏰ Search results expired. Please search again."
                )
                return

            await callback.message.edit_text(
                format_page_text(_cache[user_id]["hits"], page),
                reply_markup=create_keyboard(user_id, page, add_video=True),
                parse_mode="HTML",
            )

        elif action == "video":
            index = int(parts[1])
            if not is_cache_valid(user_id) or index >= len(_cache[user_id]["hits"]):
                await callback.message.answer(
                    "⏰ Results expired or invalid selection."
                )
                return

            hit = _cache[user_id]["hits"][index]
            status_message = await callback.message.answer("⏳ Downloading video...")

            await download_and_send_video(callback.message, status_message, hit)

            await update_statistics(callback.from_user.id, field="from_youtube")

        elif action == "sel":
            index = int(parts[1])

            if not is_cache_valid(user_id) or index >= len(_cache[user_id]["hits"]):
                await callback.message.answer(
                    "⏰ Results expired or invalid selection."
                )
                return

            if not can_download(user_id):
                await callback.message.answer(
                    "⏳ Please wait a moment before next download."
                )
                return

            _download_queue[user_id] = time.time()
            hit = _cache[user_id]["hits"][index]
            status_message = await callback.message.answer(
                f"⏳ Downloading {hit['title']}..."
            )

            await download_and_send_audio(callback.message, status_message, hit)

    except (ValueError, IndexError) as e:
        logger.error(f"Callback parsing error: {e}")
        await callback.message.answer("❌ Invalid request.")
    except Exception as e:
        logger.error(f"Callback handling error: {e}")
        await callback.message.answer("❌ Something went wrong.")


# ── download workers ──────────────────────────────────────────────────────────
async def download_and_send_audio(destination: Message, status: Message, info: Dict):
    """Download and send audio with comprehensive error handling."""
    try:
        file_path = await get_controller().download_full_track(
            info["title"], info["artist"]
        )

        if file_path and os.path.exists(file_path):
            # Verify file size and content
            file_size = Path(file_path).stat().st_size
            if file_size == 0:
                await status.edit_text("❌ Downloaded file is empty.")
                return

            await destination.answer_audio(
                FSInputFile(file_path),
                title=info["title"][:100],  # Telegram limits
                performer=info["artist"][:100],
                caption=f"🎵 <b>{info['title'][:100]}</b>\n👤 {info['artist'][:100]}",
                parse_mode="HTML",
            )

            await atomic_clear(file_path)
            await status.delete()

        else:
            await status.edit_text(
                "❌ Download failed. The track might not be available."
            )

    except Exception as e:
        logger.error(f"Audio download error: {e}")
        await status.edit_text(f"❌ Download error: {str(e)[:100]}")


async def download_and_send_video(destination: Message, status: Message, info: Dict):
    try:
        video_id = info.get("id")
        if not video_id:
            await status.edit_text("❌ Video ID not available.")
            return

        file_path = await get_controller().download_video(video_id, info["title"])

        if file_path and os.path.exists(file_path):
            # Verify file
            file_size = Path(file_path).stat().st_size
            if file_size == 0:
                await status.edit_text("❌ Downloaded video is empty.")
                return

            await destination.answer_video(
                FSInputFile(file_path),
                caption=f"🎬 <b>{info['title'][:100]}</b>",
                parse_mode="HTML",
                supports_streaming=True,
            )

            await atomic_clear(file_path)
            await status.delete()

        else:
            await status.edit_text(
                "❌ Video download failed (might be >50MB or unavailable)."
            )

    except Exception as e:
        logger.error(f"Video download error: {e}")
        await status.edit_text(f"❌ Video download error: {str(e)[:100]}")
