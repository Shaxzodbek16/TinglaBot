from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.i18n import gettext as _

from app.bot.handlers.user_handlers import get_user_by_tg_id, update_user_by_tg_id
from app.bot.keyboards.language_keyboard import language_keyboard
from app.bot.models import User

language_router = Router()


@language_router.message(F.text == "/lang")
async def ask_language(message: Message):
    user: User = await get_user_by_tg_id(message.from_user.id)
    current_lang = user.language_code
    kb = await language_keyboard(selected_lang=current_lang)
    await message.answer("🌐 Please choose your language:", reply_markup=kb)


@language_router.callback_query(F.data.startswith("set_lang:"))
async def on_language_selected(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split(":")[1]
    await update_user_by_tg_id(user_id, {"language_code": lang_code})
    await callback.message.delete()
    await callback.message.answer(_("start"))


@language_router.message(Command("developer"))
async def handle_developer_command(message: Message):
    await message.answer(
        "🤖 This bot was created by <a href='https://t.me/tmshaxzodbek'>@tmshaxzodbek</a>.\n\n"
        "🌐 Website: <a href='https://shaxzodbek.com'>Shaxzodbek/a>\n"
        "💼 LinkedIn: <a href='https://linkedin.com/in/shaxzodbek-muxtorov-59144a294'>shaxzodbek</a>\n"
        "📧 Email: <a href='mailto:muxtorovshaxzodbek16@gmail.com'>muxtorovshaxzodbek16@gmail.com</a>\n"
        "📱 GitHub: <a href='https://github.com/Shaxzodbek16'>github.com/Shaxzodbek16</a>\n"
        "📞 Phone: +998 91 526 01 12",
        parse_mode="HTML",
        disable_web_page_preview=False,
    )
