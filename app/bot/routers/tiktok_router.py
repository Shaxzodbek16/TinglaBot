from aiogram import Router, F
from aiogram.types import Message, FSInputFile

from app.bot.keyboards.general_buttons import get_music_download_button
from app.core.extensions.utils import WORKDIR

tiktok_router = Router()


@tiktok_router.message(F.text.contains("tiktok.com"))
async def handle_instagram_link(message: Message):
    await message.answer("TikTok link detected! Processing...")
    video = FSInputFile(WORKDIR.parent / "media/video.mp4")
    await message.answer_video(
        video,
        caption="Here is your video from TikTok!",
        reply_markup=get_music_download_button("tiktok"),
    )


@tiktok_router.callback_query(F.data.startswith("tiktok:"))
async def handle_instagram_callback(callback_query):
    action = callback_query.data.split(":")[1]
    if action == "download_music":
        await callback_query.answer("Downloading music from TikTok...")
        await callback_query.message.answer(
            "Music download feature is not implemented yet."
        )
