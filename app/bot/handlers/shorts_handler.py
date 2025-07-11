import logging
from pathlib import Path
from aiogram.types import Message, FSInputFile
from app.bot.controller.shorts_controller import YouTubeShortsController

logger = logging.getLogger(__name__)


class YouTubeShortsHandler:
    def __init__(self):
        self.controller = YouTubeShortsController(Path.cwd() / "media" / "youtube_shorts")

    async def handle(self, message: Message, url: str):
        try:
            status_msg = await message.answer("🔄 YouTube Shorts yuklab olinmoqda...")

            video_path = await self.controller.download_video(url)

            await status_msg.delete()
            await message.answer_video(
                FSInputFile(video_path),
                caption="✅ YouTube Shorts tayyor!"
            )

        except Exception as e:
            logger.error(f"Handler xatolik: {e}")
            await message.answer("❌ Video yuklab olishda xatolik yuz berdi")