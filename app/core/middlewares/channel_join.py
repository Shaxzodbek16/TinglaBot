from typing import Any, Awaitable, Callable, Dict, List

from aiogram import BaseMiddleware
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from app.bot.handlers.channel_handler import get_all_channels
from app.bot.keyboards.channel_keyboards import get_channel_keyboard
from app.core.settings.config import Settings, get_settings

settings: Settings = get_settings()


CHECK_CALLBACK_DATA = "check_subscription"


class CheckSubscriptionMiddleware(BaseMiddleware):
    async def _get_unsubscribed(self, bot, tg_id: int) -> List["Channel"]:
        from app.bot.models import Channel

        channels = await get_all_channels(is_active=True)
        unsubscribed: List[Channel] = []
        for channel in channels:
            chat_id = channel.channel_id or channel.link
            try:
                member = await bot.get_chat_member(chat_id, tg_id)
                if member.status in {"left", "kicked"}:
                    unsubscribed.append(channel)
            except Exception:
                unsubscribed.append(channel)
        return unsubscribed

    async def _send_prompt(
        self, event: Message | CallbackQuery, unsubscribed: List["Channel"]
    ) -> None:
        keyboard = await get_channel_keyboard(unsubscribed)
        keyboard.add(
            InlineKeyboardButton(text="✅ Check", callback_data=CHECK_CALLBACK_DATA)
        )
        channels_text = "\n".join(
            [f"@{c.link.lstrip('@')}" if c.link else c.name for c in unsubscribed]
        )
        text = (
            'Please subscribe to the following channels and press "Check":'
            f"\n{channels_text}"
        )
        if isinstance(event, Message):
            await event.answer(text, reply_markup=keyboard)
        else:
            await event.message.edit_text(text, reply_markup=keyboard)
            await event.answer()

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        bot = data["bot"]
        tg_id = (
            event.from_user.id
            if hasattr(event, "from_user") and event.from_user
            else None
        )
        if tg_id is None:
            return await handler(event, data)

        unsubscribed = await self._get_unsubscribed(bot, tg_id)

        if isinstance(event, CallbackQuery) and event.data == CHECK_CALLBACK_DATA:
            if unsubscribed:
                await self._send_prompt(event, unsubscribed)
                return
            await event.message.edit_text("✅ Subscription verified.")
            await event.answer()
            return

        if unsubscribed:
            await self._send_prompt(event, unsubscribed)
            return

        return await handler(event, data)
