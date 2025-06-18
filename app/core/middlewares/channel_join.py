from aiogram import BaseMiddleware
from aiogram.types import (
    TelegramObject,
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from typing import Callable, Awaitable, Any, Dict
from aiogram.exceptions import TelegramBadRequest
import logging

from app.bot.handlers.channel_handler import get_all_channels
from app.bot.models import Channel
from app.core.settings.config import get_settings, Settings

settings: Settings = get_settings()
admins = settings.admins_list
logger = logging.getLogger(__name__)


class CheckSubscriptionMiddleware(BaseMiddleware):
    def __init__(self, skip_updates: bool = False):
        self.skip_updates = skip_updates
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not hasattr(event, "from_user") or not event.from_user:
            return await handler(event, data)

        user_id = event.from_user.id

        if user_id in admins:
            return await handler(event, data)

        bot = data.get("bot")
        if not bot:
            logger.error("Bot instance not found in middleware data")
            return await handler(event, data)

        is_subscribed, unsubscribed_channels = await self._check_user_subscriptions(
            bot, user_id
        )

        if not is_subscribed:
            await self._send_subscription_message(event, bot, unsubscribed_channels)
            return None

        return await handler(event, data)

    async def _check_user_subscriptions(
        self, bot, user_id: int
    ) -> tuple[bool, list[Channel]]:
        try:
            channels = await get_all_channels(is_active=True)

            if not channels:
                return True, []

            unsubscribed_channels = []

            for channel in channels:
                try:
                    member = await bot.get_chat_member(channel.channel_id, user_id)
                    if member.status in ["left", "kicked"]:
                        unsubscribed_channels.append(channel)
                except TelegramBadRequest as e:
                    logger.warning(
                        f"Error checking subscription for channel {channel.channel_id}: {e}"
                    )
                    unsubscribed_channels.append(channel)
                except Exception as e:
                    logger.error(
                        f"Unexpected error checking channel {channel.channel_id}: {e}"
                    )
                    unsubscribed_channels.append(channel)

            return len(unsubscribed_channels) == 0, unsubscribed_channels

        except Exception as e:
            logger.error(f"Error in subscription check: {e}")
            return False, []

    async def _send_subscription_message(
        self, event: TelegramObject, bot, unsubscribed_channels: list[Channel]
    ):
        try:
            message_text = self._create_subscription_message(unsubscribed_channels)
            keyboard = self._create_subscription_keyboard(unsubscribed_channels)

            if isinstance(event, Message):
                await bot.send_message(
                    chat_id=event.chat.id,
                    text=message_text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )
            elif isinstance(event, CallbackQuery):
                await event.answer("Please subscribe to all channels first!")

                if event.message:
                    try:
                        await bot.edit_message_text(
                            chat_id=event.message.chat.id,
                            message_id=event.message.message_id,
                            text=message_text,
                            reply_markup=keyboard,
                            parse_mode="HTML",
                        )
                    except TelegramBadRequest:
                        await bot.send_message(
                            chat_id=event.message.chat.id,
                            text=message_text,
                            reply_markup=keyboard,
                            parse_mode="HTML",
                        )

        except Exception as e:
            logger.error(f"Error sending subscription message: {e}")

    def _create_subscription_message(self, unsubscribed_channels: list[Channel]) -> str:
        message_lines = [
            "🔒 <b>Subscription Required</b>",
            "",
            "To use this bot, you need to subscribe to the following channels:",
            "",
        ]

        for i, channel in enumerate(unsubscribed_channels, 1):
            channel_name = (
                channel.title
                if hasattr(channel, "title") and channel.title
                else f"Channel {i}"
            )
            message_lines.append(f"{i}. {channel_name}")

        message_lines.extend(
            [
                "",
                "After subscribing to all channels, click the 'Check Subscription' button below.",
                "",
                "📢 <i>Make sure you don't leave the channels after subscribing!</i>",
            ]
        )

        return "\n".join(message_lines)

    def _create_subscription_keyboard(
        self, unsubscribed_channels: list[Channel]
    ) -> InlineKeyboardMarkup:
        keyboard = []

        # Add subscription buttons
        for channel in unsubscribed_channels:
            channel_name = (
                channel.title
                if hasattr(channel, "title") and channel.title
                else "Subscribe"
            )

            if hasattr(channel, "username") and channel.username:
                channel_url = f"https://t.me/{channel.username}"
            else:
                channel_url = f"https://t.me/c/{str(channel.channel_id)[4:]}"
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text=f"📢 Subscribe to {channel_name}", url=channel_url
                    )
                ]
            )
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="✅ Check Subscription", callback_data="check_subscription"
                )
            ]
        )

        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    async def _handle_subscription_check(self, callback_query: CallbackQuery, bot):
        user_id = callback_query.from_user.id

        is_subscribed, unsubscribed_channels = await self._check_user_subscriptions(
            bot, user_id
        )

        if is_subscribed:
            await callback_query.answer("✅ Great! You're subscribed to all channels.")
            try:
                await bot.delete_message(
                    chat_id=callback_query.message.chat.id,
                    message_id=callback_query.message.message_id,
                )
            except TelegramBadRequest:
                pass
        else:
            await callback_query.answer(
                "❌ You're still not subscribed to all channels!", show_alert=True
            )
            await self._send_subscription_message(
                callback_query, bot, unsubscribed_channels
            )
