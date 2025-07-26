from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_admin_panel_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📁 Users excel"), KeyboardButton(text="📊 Statistics")],
        [KeyboardButton(text="🔧 Settings"), KeyboardButton(text="📈 Channels")],
        [
            KeyboardButton(text="💲 Fill Balance"),
            KeyboardButton(text="Remove from balance"),
        ],
        [KeyboardButton(text="🔙 Back to Main Menu")],
    ]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Choose an admin action 🔧",
    )


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_channel_crud_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text="➕ Add Channel"),
            KeyboardButton(text="📋 View Channels"),
        ],
        [KeyboardButton(text="🔙 Back to Admin Panel")],
    ]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Select channel action 📡",
    )


def settings_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text="Update Tokens per Referral"),
            KeyboardButton(text="Update Premium price"),
        ],
        [
            KeyboardButton(text="Send Message to All Users"),
            KeyboardButton(text="🔙 Back to Admin Panel"),
        ],
    ]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Settings options ⚙️",
    )


ask_media_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="✅ Add Media"), KeyboardButton(text="⏭ Skip Media")],
        [KeyboardButton(text="🔙 Back to Admin Panel")],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)

back_to_admin_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔙 Back to Admin Panel")]],
    resize_keyboard=True,
    one_time_keyboard=True,
)
