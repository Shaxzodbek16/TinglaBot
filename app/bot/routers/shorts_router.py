import logging
from aiogram import Router, F
from aiogram.types import Message
from app.bot.handlers.shorts_handler import YouTubeShortsHandler

logger = logging.getLogger(__name__)
youtube_shorts_router = Router()
handler = YouTubeShortsHandler()


def extract_shorts_url(text: str) -> str:
    """YouTube Shorts URL ni ajratib olish"""
    words = text.split()
    for word in words:
        if "youtube.com/shorts" in word or "youtu.be" in word:
            return word
    return ""


@youtube_shorts_router.message(F.text.contains("youtube.com/shorts") | F.text.contains("youtu.be"))
async def process_shorts(message: Message):
    try:
        url = extract_shorts_url(message.text)
        if not url:
            return

        await handler.handle(message, url)

    except Exception as e:
        logger.exception("Router xatolik:")
        await message.answer("❌ Xatolik yuz berdi")