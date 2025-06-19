from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from app.bot.handlers.admin import get_token_per_referral
from app.bot.handlers.user_handlers import get_referral_count, get_token_count
from app.core.settings.config import get_settings, Settings

user_router = Router()
settings: Settings = get_settings()
bot = Bot(settings.BOT_TOKEN)


@user_router.message(F.text == "📥 Refer Friends and Earn")
async def handle_refer_friends(message: Message):
    count = await get_referral_count(message.from_user.id)
    token = await get_token_count(message.from_user.id)
    token_count = await get_token_per_referral()
    bot_info = await bot.get_me()

    if not bot_info.username:
        await message.answer(
            "❌ Error: Bot username is not set. Please contact the bot administrator."
        )
        return

    referral_link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"

    text = (
        "🎉 <b>Referral Program</b>\n\n"
        f"👥 <b>Friends Referred:</b> <code>{count}</code>\n"
        f"🎟 <b>Your Tokens:</b> <code>{token}</code>\n\n"
        f"📣 Share this bot with your friends and earn {token_count} exclusive tokens!\n"
        "🔗 Use your personal referral link below ⬇️"
    )

    share_button = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Share with Friends",
                    url=f"https://t.me/share/url?url={referral_link}&text=🎁 Join and earn tokens with me!",
                )
            ]
        ]
    )

    await message.answer(text, parse_mode="HTML", reply_markup=share_button)
