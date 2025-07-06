from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from app.bot.handlers.pinterest_handler import download_pinterest_media
import logging
from pathlib import Path

pinterest_router = Router()
logger = logging.getLogger(__name__)


@pinterest_router.message(F.text.regexp(r"(https?://)?(www\.)?(pin\.it|pinterest\.com)/[^\s]+"))
async def handle_pinterest_link(message: Message):
    url = message.text.strip()

    await message.answer("📥 Detected pinterest link. Downloading...")

    try:
        result = await download_pinterest_media(url)

        if not result:
            await message.answer("❌ Can't download pinterest media.")
            return

        file_path, media_type = result

        if not Path(file_path).exists():
            await message.answer("❌ No available media found.")
            return

        if media_type == "video":
            await message.answer_video(FSInputFile(file_path), supports_streaming=True)
        elif media_type == "image":
            await message.answer_photo(FSInputFile(file_path), supports_streaming=True)
        else:
            await message.answer_document(FSInputFile(file_path))

        logger.info(f"✅ Pinterestdan {media_type} yuborildi: {file_path}")

    except Exception as e:
        logger.error(f"Pinterest yuklab olish xatosi: {e}")
        await message.answer("❌ Error occured.")
