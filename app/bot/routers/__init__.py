from aiogram import Router

from app.bot.routers.admin_router import admin_router
from app.bot.routers.start_router import start_router
from app.bot.routers.language_router import language_router
from app.bot.routers.instagram_router import instagram_router
from app.bot.routers.tiktok_router import tiktok_router
from app.bot.routers.snapchat_router import snapchat_router
from app.bot.routers.likee_router import likee_router
from app.bot.routers.user_router import user_router

v1_router = Router()

v1_router.include_routers(
    start_router,
    language_router,
    instagram_router,
    tiktok_router,
    snapchat_router,
    likee_router,
    user_router,
    admin_router,
)

__all__ = ("v1_router",)
