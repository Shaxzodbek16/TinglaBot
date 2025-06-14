from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from app.bot.extensions.clear import atomic_clear
from app.bot.handlers.instagram_handler import (
    download_instagram_video_only_mp4,
    validate_instagram_url,
)
from app.bot.keyboards.general_buttons import get_music_download_button
from app.bot.handlers.backup_handler import get_from_backup, add_to_backup
from app.core.settings.config import get_settings, Settings

settings: Settings = get_settings()

instagram_router = Router()


@instagram_router.message(F.text.contains("instagram.com"))
async def handle_instagram_link(message: Message):
    await message.answer("Instagram link detected! Processing...")
    instagram_url = validate_instagram_url(message.text)
    backup = await get_from_backup(url=instagram_url)
    if backup is not None:
        await message.bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=settings.CHANNEL_ID,
            message_id=backup.message_id,
        )
        await message.answer(
            "This video has already been processed. Here it is again:",
            reply_markup=get_music_download_button("instagram"),
        )
        return
    video_path = await download_instagram_video_only_mp4(instagram_url)
    video = FSInputFile(video_path)
    await message.answer_video(
        video,
        caption="Here is your video from Instagram!",
        reply_markup=get_music_download_button("instagram"),
    )
    await add_to_backup(url=instagram_url, video_path=video_path)
    await atomic_clear(video_path)


@instagram_router.callback_query(F.data.startswith("instagram:"))
async def handle_instagram_callback(callback_query):
    action = callback_query.data.split(":")[1]
    if action == "download_music":
        await callback_query.answer("Downloading music from Instagram...")
        await callback_query.message.answer(
            "Music download feature is not implemented yet."
        )
