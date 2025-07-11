from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from app.bot.handlers.admin import get_token_per_referral
from app.bot.handlers.user_handlers import get_referral_count
from app.core.settings.config import get_settings, Settings

user_router = Router()
settings: Settings = get_settings()
bot = Bot(settings.BOT_TOKEN)


@user_router.message(F.text == __("refer_button"))
async def handle_refer_friends(message: Message):
    count = await get_referral_count(message.from_user.id)
    token_count = await get_token_per_referral()
    bot_info = await bot.get_me()

    if not bot_info.username:
        await message.answer(_("refer_bot_username_missing"))
        return

    referral_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"

    text = (
        _("refer_message")
        .format(count=count, token_count=token_count, referral_link=referral_link)
    )

    share_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=_("refer_share_btn"),
                    url=f"https://t.me/share/url?url={referral_link}&text=🎁 " + _("refer_share_text"),
                )
            ]
        ]
    )

    await message.answer(text, parse_mode="HTML", reply_markup=share_button)