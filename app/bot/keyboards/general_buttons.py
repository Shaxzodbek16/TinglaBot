def get_music_download_button(media_name: str):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = [
        InlineKeyboardButton(
            text="Download music", callback_data=f"{media_name}:download_music"
        ),
    ]

    return InlineKeyboardMarkup(row_width=2, inline_keyboard=[buttons])
