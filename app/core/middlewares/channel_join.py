from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from app.bot.keyboards.channel_keyboards import get_channel_keyboard
from app.core.settings.config import get_settings, Settings

settings: Settings = get_settings()


class CheckSubscriptionMiddleware(BaseMiddleware):
    pass
