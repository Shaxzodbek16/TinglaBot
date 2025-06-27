import asyncio

from aiogram import Bot
from app.core.settings.config import get_settings, Settings

settings: Settings = get_settings()

bot = Bot(token=settings.BOT_TOKEN)


async def log_out(sleep_time: int = 5) -> None:
    await asyncio.sleep(sleep_time)
    await bot.log_out()
