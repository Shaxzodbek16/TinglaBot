from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from app.bot.handlers.channel_handler import get_all_channels
from app.bot.models import Channel


async def channels_list_keyboard() -> InlineKeyboardMarkup:
    channels: list[Channel] = await get_all_channels()

    inline_keyboard = [
        row
        for ch in channels
        for row in (
            [
                InlineKeyboardButton(
                    text=f"📺 {ch.name}", callback_data=f"channel:info:{ch.id}"
                ),
                InlineKeyboardButton(text="🔗 View Link", url=ch.link),
            ],
            [
                InlineKeyboardButton(
                    text="✅" if ch.is_active else "❌",
                    callback_data=f"channel:toggle:{ch.id}",
                ),
                InlineKeyboardButton(
                    text="✏️ Update", callback_data=f"channel:update:{ch.id}"
                ),
                InlineKeyboardButton(
                    text="🗑️ Delete", callback_data=f"channel:delete:{ch.id}"
                ),
            ],
        )
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


active_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Yes"), KeyboardButton(text="❌ No")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


def skip_kb(label: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=label)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
