from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery

from app.bot.extensions.clear import atomic_clear
from app.bot.handlers.instagram_handler import (
    download_instagram_video_only_mp4,
    validate_instagram_url,
    extract_audio_from_instagram_video,
)
from app.bot.keyboards.general_buttons import get_music_download_button
from app.bot.handlers.backup_handler import get_from_backup, add_to_backup
from app.bot.routers.music_router import (
    format_page_text,
    create_keyboard,
    get_controller,
    _cache,
)
from app.core.settings.config import get_settings, Settings
from app.bot.handlers import shazam_handler as shz

settings: Settings = get_settings()

instagram_router = Router()
user_sessions = {}  # Session storage

import time


@instagram_router.message(F.text.contains("instagram.com"))
async def handle_instagram_link(message: Message):
    await message.answer("📎 Instagram link detected! Processing...")

    user_id = message.from_user.id
    instagram_url = validate_instagram_url(message.text)

    # Saqlab qo‘yamiz
    user_sessions[user_id] = {"url": instagram_url}

    # Oldin yuklangan bo‘lsa, backup dan jo‘natamiz
    backup = await get_from_backup(url=instagram_url)
    if backup:
        user_sessions[user_id]["backup_message_id"] = backup.message_id
        await message.bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=settings.CHANNEL_ID,
            message_id=backup.message_id,
        )
        await message.answer(
            "✅ This video has already been processed. Here it is again:",
            reply_markup=get_music_download_button("instagram"),
        )
        return

    # Video yuklash
    video_path = await download_instagram_video_only_mp4(instagram_url)
    user_sessions[user_id]["video_path"] = video_path

    await message.answer_video(
        FSInputFile(video_path),
        caption="📽 Here is your video from Instagram!",
        reply_markup=get_music_download_button("instagram"),
    )

    await add_to_backup(url=instagram_url, video_path=video_path)
    await atomic_clear(video_path)


@instagram_router.callback_query(F.data.startswith("instagram:"))
async def handle_instagram_callback(callback_query: CallbackQuery):
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
        # 1. Extract audio
        audio_path = await extract_audio_from_instagram_video(session["url"])
        if not audio_path:
            await callback_query.message.answer("❌ Could not extract audio.")
            return

        # 2. Recognize via Shazam
        shazam_hits = await shz.recognise_music_from_audio(audio_path)
        if not shazam_hits:
            await callback_query.message.answer(
                "😕 Could not recognize any music in this video."
            )
            return

        track = shazam_hits[0]["track"]
        title = track["title"]
        artist = track["subtitle"]
        search_query = f"{title} {artist}"

        # 3. Search on YouTube
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

        # 4. Display result
        await callback_query.message.answer(
            f"🎶 <b>{title}</b>\n👤 {artist}",
            parse_mode="HTML",
        )

        # ✅ Cache hits to show buttons
        _cache[user_id] = {
            "hits": youtube_hits,
            "timestamp": time.time(),
        }

        await callback_query.message.answer(
            format_page_text(youtube_hits, 0),
            reply_markup=create_keyboard(user_id, 0, add_video=True),
            parse_mode="HTML",
        )

        # 5. Clean up
        await atomic_clear(audio_path)

    except Exception as e:
        print(f"Error during recognition: {str(e)}")
        await callback_query.message.answer(
            "❌ Something went wrong during recognition."
        )

    # Clear session
    user_sessions.pop(user_id, None)
