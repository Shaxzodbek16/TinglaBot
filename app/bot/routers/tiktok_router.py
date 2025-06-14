from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from app.bot.extensions.clear import atomic_clear
from app.bot.handlers.backup_handler import get_from_backup, add_to_backup
from app.bot.handlers.tiktok_handler import get_tiktok_video, validate_tiktok_url
from app.bot.keyboards.general_buttons import get_music_download_button
from app.core.settings.config import get_settings, Settings

settings: Settings = get_settings()

tiktok_router = Router()


@tiktok_router.message(F.text.contains("tiktok.com"))
async def handle_tiktok_link(message: Message):
    await message.answer("TikTok link detected! Processing...")
    tiktok_url = validate_tiktok_url(message.text)
    backup = await get_from_backup(url=tiktok_url)
    if backup is not None:
        await message.bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=settings.CHANNEL_ID,
            message_id=backup.message_id,
            caption="This video has already been processed. Here it is again:",
            reply_markup=get_music_download_button("tiktok"),
        )
        return
    video_path = await get_tiktok_video(tiktok_url)
    video = FSInputFile(video_path)
    await message.answer_video(
        video,
        caption="Here is your video from TikTok!",
        reply_markup=get_music_download_button("tiktok"),
    )
    await add_to_backup(url=tiktok_url, video_path=video_path)
    await atomic_clear(video_path)


@tiktok_router.callback_query(F.data.startswith("tiktok:"))
async def handle_tiktok_callback(callback_query):
    action = callback_query.data.split(":")[1]
    if action == "download_music":
        await callback_query.answer("Downloading music from TikTok...")
        await callback_query.message.answer(
            "Music download feature is not implemented yet."
        )
