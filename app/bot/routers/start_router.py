from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CommandObject

from app.bot.handlers.user_handlers import get_user_by_tg_id, create_user
from app.bot.handlers.referral_handler import add_referral
from app.bot.keyboards.language_keyboard import language_keyboard
from app.bot.models import User

start_router = Router()


@start_router.message(CommandStart(deep_link=True))
async def handle_start(message: Message, command: CommandObject):
    await create_user(message)

    if command.args and command.args.isdigit():
        await add_referral(int(message.from_user.id), int(command.args))

    user: User = await get_user_by_tg_id(message.from_user.id)
    if user.language_code is None:
        kb = await language_keyboard(selected_lang=None)
        await message.answer(
            "👋 Welcome! Please choose your language:", reply_markup=kb
        )
    else:
        bot_username = (await message.bot.get_me()).username
        link = user.get_referral_link(bot_username)
        await message.answer("start\n" + link)
