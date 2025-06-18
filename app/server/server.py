import asyncio, logging, sys

from aiogram import Bot, Dispatcher
from aiogram.utils.i18n import I18n

from app.bot.routers import v1_router
from app.core.settings.config import get_settings, Settings
from app.core.extensions.utils import WORKDIR
from aiogram.utils.i18n.middleware import FSMI18nMiddleware
from app.core.middlewares.channel_join import CheckSubscriptionMiddleware
from app.server.init import init

settings: Settings = get_settings()
i18n = I18n(path=WORKDIR / "locales", default_locale="uz", domain="messages")
bot = Bot(settings.BOT_TOKEN)


async def main() -> None:
    init()

    i18n_middleware = FSMI18nMiddleware(i18n)
    dp = Dispatcher()
    dp.message.middleware(i18n_middleware)
    dp.callback_query.middleware(i18n_middleware)

    # dp.message.middleware(CheckSubscriptionMiddleware())
    # dp.callback_query.middleware(CheckSubscriptionMiddleware())

    dp.include_router(v1_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
