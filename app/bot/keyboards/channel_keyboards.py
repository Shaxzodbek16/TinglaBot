from app.bot.models import Channel
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def get_channel_keyboard(channels: list[Channel]):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        if channel.is_active:
            button = InlineKeyboardButton(
                text=channel.name,
                url=f"https://t.me/{channel.link.lstrip('@')}",
            )
            keyboard.add(button)
    return keyboard
