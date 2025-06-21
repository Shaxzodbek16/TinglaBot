from aiogram import Router

music_router = Router()


@music_router.message()
async def handle_music_request(message):
    await message.answer("music")
