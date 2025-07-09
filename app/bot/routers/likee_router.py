from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.utils.i18n import gettext as _

from app.bot.extensions.clear import atomic_clear
from app.bot.handlers.likee_handler import (
    download_likee_video_only_mp4,
    validate_likee_url,
)
from app.bot.handlers.statistics_handler import update_statistics
from app.bot.keyboards.general_buttons import get_music_download_button
from app.core.settings.config import get_settings, Settings

settings: Settings = get_settings()
likee_router = Router()


@likee_router.message(F.text.contains("likee.video"))
async def handle_likee_link(message: Message):
    await message.answer(_("likee_detected"))
    likee_url = validate_likee_url(message.text)
    video_path = await download_likee_video_only_mp4(likee_url)
    video = FSInputFile(video_path)

    await message.answer_video(
        video,
        caption=_("likee_video_ready"),
        reply_markup=get_music_download_button("likee"),
        supports_streaming=True,
    )
    await atomic_clear(video_path)
    await update_statistics(message.from_user.id, field="from_like")


@likee_router.callback_query(F.data.startswith("likee:"))
async def handle_likee_callback(callback_query):
    action = callback_query.data.split(":")[1]
    if action == "download_music":
        await callback_query.answer(_("likee_downloading_music"))
        await callback_query.message.answer(_("likee_music_not_implemented"))
