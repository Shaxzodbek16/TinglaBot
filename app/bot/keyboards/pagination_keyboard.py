from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_track_keyboard(
    data: dict, next_page: str | None = None, prev_page: str | None = None
) -> InlineKeyboardMarkup:
    messages = []
    buttons = []
