from aiogram import Router

v1_router = Router()

from app.bot.routers.start_router import start_router
from app.bot.routers.language_router import language_router
from app.bot.routers.instagram_router import instagram_router
from app.bot.routers.tiktok_router import tiktok_router

v1_router.include_routers(
    start_router, language_router, instagram_router, tiktok_router
)

__all__ = ("v1_router",)
