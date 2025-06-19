from typing import Callable, Awaitable, Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import Message
from app.bot.models import Channel
from app.core.databases.postgres import get_general_session
from sqlalchemy.future import select
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from app.core.settings.config import get_settings, Settings

config: Settings = get_settings()


async def get_active_channels() -> list[Channel]:
    async with get_general_session() as session:
        query = select(Channel).where(Channel.is_active == True)
        result = await session.execute(query)
        return result.scalars().all()


async def is_subscribed(user_id: int, channel_id: int, bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramBadRequest:
        return False


class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if (
                event.text
                and event.text.startswith("/start")
                or event.text in ["🇺🇿 O‘zbekcha", "🇷🇺 Русский", "🇬🇧 English"]
            ):
                return await handler(event, data)

            user_id = event.from_user.id
            bot = data["bot"]
            channels = await get_active_channels()
            not_joined = []

            for channel in channels:
                if not await is_subscribed(user_id, channel.channel_id, bot):
                    not_joined.append(channel)

            if not_joined:
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=f"📢 {ch.name}", url=ch.link)]
                        for ch in not_joined
                    ]
                    + [
                        [
                            InlineKeyboardButton(
                                text="✅ Check", callback_data="check_subscription"
                            )
                        ]
                    ]
                )

                await event.answer(
                    text="😕 To use this bot, please join the channels below first:",
                    reply_markup=kb,
                )
                return None

        return await handler(event, data)
