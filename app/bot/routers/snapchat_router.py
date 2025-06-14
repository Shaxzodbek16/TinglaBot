from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from app.bot.extensions.clear import atomic_clear
from app.bot.handlers.backup_handler import get_from_backup, add_to_backup
from app.bot.handlers.tiktok_handler import get_tiktok_video, validate_tiktok_url
from app.bot.keyboards.general_buttons import get_music_download_button
from app.core.settings.config import get_settings, Settings

settings: Settings = get_settings()

snapchat_router = Router()


@snapchat_router.message(F.text.contains("snapchat.com"))
async def handle_snapchat_link(message: Message):
    await message.answer(
        "Snapchat link detected! Processing...",
        reply_markup=get_music_download_button("snapchat"),
    )


@snapchat_router.callback_query(F.data.startswith("snapchat:"))
async def handle_instagram_callback(callback_query):
    action = callback_query.data.split(":")[1]
    if action == "download_music":
        await callback_query.answer("Downloading music from SnapChat...")
        await callback_query.message.answer(
            "Music download feature is not implemented yet."
        )
