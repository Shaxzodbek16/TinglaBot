from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _

from app.bot.handlers.user_handlers import get_user_by_tg_id

referral_router = Router()


@referral_router.message(Command("referral"))
async def send_referral_link(message: Message):
    user = await get_user_by_tg_id(message.from_user.id)
    bot_username = (await message.bot.get_me()).username
    link = user.get_referral_link(bot_username)

    await message.answer(_("your_referral_link").format(link=link))


@referral_router.callback_query(F.data == 'invite_friends')
async def invite_friends(callback_query: CallbackQuery):
    user = await get_user_by_tg_id(callback_query.from_user.id)
    bot_username = (await callback_query.bot.get_me()).username
    link = user.get_referral_link(bot_username)

    await callback_query.message.answer(_("your_referral_link").format(link=link))
