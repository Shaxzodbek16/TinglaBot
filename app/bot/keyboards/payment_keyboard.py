from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_payment_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Activate Subscription", callback_data="activate_subscription"), InlineKeyboardButton(text="Invite Friends", callback_data="invite_friends"),]
        ])


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Confirm", callback_data="confirm_payment"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_payment")
            ]
        ]
    )