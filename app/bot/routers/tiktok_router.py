import time

from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery

from app.bot.extensions.clear import atomic_clear
from app.bot.handlers.backup_handler import get_from_backup, add_to_backup
from app.bot.handlers.tiktok_handler import (
    get_tiktok_video,
    validate_tiktok_url,
    extract_audio_from_tiktok_video_smart,
)
from app.bot.handlers import shazam_handler as shz
from app.bot.routers.music_router import (
    get_controller,
    format_page_text,
    create_keyboard,
    _cache,
)
from app.bot.keyboards.general_buttons import get_music_download_button
from app.core.settings.config import get_settings, Settings

settings: Settings = get_settings()
tiktok_router = Router()
user_sessions = {}


@tiktok_router.message(F.text.contains("tiktok.com"))
async def handle_tiktok_link(message: Message):
    await message.answer("📎 TikTok link detected! Processing...")

    user_id = message.from_user.id
    tiktok_url = validate_tiktok_url(message.text)
    user_sessions[user_id] = {"url": tiktok_url}

    backup = await get_from_backup(url=tiktok_url)
    if backup:
        user_sessions[user_id]["backup_message_id"] = backup.message_id
        await message.bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=settings.CHANNEL_ID,
            message_id=backup.message_id,
        )
        await message.answer(
            "✅ This video has already been processed. Here it is again:",
            reply_markup=get_music_download_button("tiktok"),
        )
        return

    try:
        video_path = await get_tiktok_video(tiktok_url)
        user_sessions[user_id]["video_path"] = video_path

        await message.answer_video(
            FSInputFile(video_path),
            caption="📽 Here is your video from TikTok!",
            reply_markup=get_music_download_button("tiktok"),
        )

        await add_to_backup(url=tiktok_url, video_path=video_path)
        await atomic_clear(video_path)

    except Exception as e:
        await message.answer(f"❌ Failed to download video: {e}")


@tiktok_router.callback_query(F.data.startswith("tiktok:"))
async def handle_tiktok_callback(callback_query: CallbackQuery):
    action = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id

    if action != "download_music":
        await callback_query.answer("❌ Unknown action.")
        return

    await callback_query.answer("🔍 Extracting and recognizing music...")

    session = user_sessions.get(user_id)
    if not session or not session.get("url"):
        await callback_query.message.answer(
            "❌ Session expired. Please resend the link."
        )
        return

    try:
        # 1. Audio ajratish
        audio_path = await extract_audio_from_tiktok_video_smart(session["url"])
        if not audio_path:
            await callback_query.message.answer("❌ Could not extract audio.")
            return

        # 2. Shazam orqali aniqlash
        shazam_hits = await shz.recognise_music_from_audio(audio_path)
        if not shazam_hits:
            await callback_query.message.answer(
                "😕 Could not recognize any music in this video."
            )
            return

        # 3. YouTube qidiruv
        track = shazam_hits[0]["track"]
        title, artist = track["title"], track["subtitle"]
        search_query = f"{title} {artist}"

        youtube_hits = await get_controller().search(search_query)
        if not youtube_hits:
            youtube_hits = [
                get_controller().ytdict_to_info(
                    {
                        "title": title,
                        "artist": artist,
                        "duration": 0,
                        "id": track.get("key", ""),
                    }
                )
            ]

        # 4. Natijani ko‘rsatish
        await callback_query.message.answer(
            f"🎶 <b>{title}</b>\n👤 {artist}",
            parse_mode="HTML",
        )
        _cache[user_id] = {
            "hits": youtube_hits,
            "timestamp": time.time(),
        }

        await callback_query.message.answer(
            format_page_text(youtube_hits, 0),
            reply_markup=create_keyboard(user_id, 0, add_video=True),
            parse_mode="HTML",
        )

        await atomic_clear(audio_path)

    except Exception as e:
        await callback_query.message.answer(
            f"❌ Error during recognition: {str(e)[:100]}"
        )

    user_sessions.pop(user_id, None)
