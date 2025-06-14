from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.handlers.user_handlers import get_user_by_tg_id, create_user
from app.bot.keyboards.language_keyboard import language_keyboard
from app.bot.models import User

start_router = Router()


@start_router.message(CommandStart())
async def handle_start(message: Message):
    await create_user(message)
    user: User = await get_user_by_tg_id(message.from_user.id)
    if user.language_code is None:
        kb = await language_keyboard(selected_lang=None)
        await message.answer(
            "👋 Welcome! Please choose your language:", reply_markup=kb
        )
    else:
        await message.answer("start")
