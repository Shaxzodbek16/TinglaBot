import logging
import time
from pathlib import Path
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.utils.i18n import gettext as _

from app.bot.controller.group_controller import GroupController
from app.bot.extensions.clear import atomic_clear
from app.bot.handlers.statistics_handler import update_statistics
from app.bot.handlers.tiktok_handler import extract_audio_from_tiktok_video_smart
from app.bot.handlers import shazam_handler as shz
from app.bot.routers.music_router import (
    get_controller,
    format_page_text,
    create_keyboard,
    _cache,
)
from app.bot.keyboards.general_buttons import get_music_download_button

logger = logging.getLogger(__name__)

# Group router
group_router = Router()
group_controller = GroupController()

# User sessions for music download
user_sessions = {}


# Guruh commandlari uchun alohida filterlar
@group_router.message(Command("help"))
async def group_help_command(message: Message):
    """Guruh va shaxsiy chat uchun yordam"""

    # Guruh chatida bo'lsa
    if message.chat.type in ["group", "supergroup"]:
        help_text = """
🤖 <b>Guruhda ishlash</b>

<b>Qanday ishlatish:</b>
• Social media linkini yuboring
• Botni mention qiling (@bot_username)
• Xabarga reply qiling

<b>Qo'llab-quvvatlanadigan platformalar:</b>
• TikTok
• Pinterest  
• Threads
• Twitter/X
• Likee
• Snapchat
• YouTube Shorts

<b>Buyruqlar:</b>
/platforms - Platformalar ro'yxati
/help - Bu yordam xabari

<b>Eslatma:</b> Bot faqat media linklariga javob beradi
"""
        await message.reply(help_text, parse_mode="HTML")
        return  # Bu muhim - keyingi handlerlar ishlamasin

    # Agar shaxsiy chatda bo'lsa, keyingi handlerlarga o'tkazish
    # (return qilmaslik orqali)


@group_router.message(Command("platforms"))
async def show_supported_platforms_command(message: Message):
    """Platformalar ro'yxati - faqat guruhlar uchun"""

    # Faqat guruh chatlarida ishlaydi
    if message.chat.type in ["group", "supergroup"]:
        platforms = group_controller.get_supported_platforms()

        text = "🌐 Qo'llab-quvvatlanadigan platformalar:\n\n"
        for i, platform in enumerate(platforms, 1):
            text += f"{i}. {platform}\n"

        text += "\n📝 Foydalanish: Guruhga link yuboring yoki botni mention qiling"

        await message.reply(text)
        return


# Link lar uchun handler
@group_router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message):
    """Guruh xabarlarini qayta ishlash"""

    # Agar command bo'lsa, skip qilish
    if message.text and message.text.startswith('/'):
        return

    # Faqat social media linklar mavjud bo'lganda javob berish
    if not message.text or not group_controller.is_social_media_link(message.text):
        return

    # Bot mention qilingan yoki reply qilinganida ishga tushishi
    bot_mentioned = await _is_bot_mentioned(message)

    # Agar bot mention qilinmagan bo'lsa va avtomatik javob berish kerak emas bo'lsa, return
    if not bot_mentioned and not _should_respond_automatically(message):
        return

    # URLlarni ajratib olish
    urls = group_controller.extract_urls(message.text)
    if not urls:
        return

    # Processing xabar yuborish
    processing_msg = await message.reply(
        "🔄 Media yuklab olinmoqda...",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_download")
        ]])
    )

    try:
        downloaded_files = []
        failed_urls = []

        for url in urls:
            try:
                result = await group_controller.download_media(url)

                if result["success"] and result["files"]:
                    downloaded_files.extend(result["files"])
                    # URL va platformani session'da saqlash
                    user_id = message.from_user.id
                    if user_id not in user_sessions:
                        user_sessions[user_id] = []

                    platform = group_controller.detect_platform(url)
                    user_sessions[user_id].append({
                        "url": url,
                        "platform": platform.value if platform else "unknown",
                        "files": result["files"]
                    })
                else:
                    failed_urls.append((url, result.get("message", "Noma'lum xatolik")))

            except Exception as e:
                logger.error(f"Download error for {url}: {e}")
                failed_urls.append((url, f"Xatolik: {str(e)}"))

        # Processing xabarini o'chirish
        try:
            await processing_msg.delete()
        except:
            pass

        # Natijalarni yuborish
        if downloaded_files:
            await _send_media_files(message, downloaded_files)

            # Muvaffaqiyat xabari music download tugmasi bilan
            success_text = f"✅ {len(downloaded_files)} ta fayl yuklandi"

            if failed_urls:
                success_text += f"\n❌ {len(failed_urls)} ta link yuklanmadi"

            # Music download tugmasini qo'shish
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🎵 Musiqa yuklash",
                    callback_data=f"group_music:{message.from_user.id}"
                )
            ]])

            await message.reply(success_text, reply_markup=keyboard)

        elif failed_urls:
            # Faqat xatolar bo'lsa
            error_text = "❌ Hech qanday media yuklanmadi:\n\n"
            for url, error in failed_urls:
                platform = group_controller.detect_platform(url)
                platform_name = platform.value if platform else "Noma'lum"
                error_text += f"• {platform_name}: {error}\n"

            await message.reply(error_text[:4000])  # Telegram limit

        # Statistics yangilash
        try:
            await update_statistics(message.from_user.id, field="from_group")
        except:
            pass

    except Exception as e:
        logger.error(f"Group handler error: {e}")
        try:
            await processing_msg.edit_text(
                f"❌ Xatolik yuz berdi: {str(e)}",
                reply_markup=None
            )
        except:
            pass


@group_router.callback_query(F.data == "cancel_download")
async def cancel_download(callback):
    """Yuklab olishni bekor qilish"""
    try:
        await callback.message.edit_text("❌ Yuklab olish bekor qilindi")
        await callback.answer()
    except:
        await callback.answer("❌ Bekor qilindi")


# Video yuborish qismini o'zgartiring
async def _send_media_files(message: Message, files: list):
    """Media fayllarni yuborish - video fayllarni saqlab qolish"""
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    for file_info in files:
        try:
            file_path = Path(file_info["path"])

            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue

            # Fayl hajmini tekshirish
            if file_path.stat().st_size > MAX_FILE_SIZE:
                await message.reply(f"❌ Fayl juda katta: {file_path.name}")
                continue

            file_input = FSInputFile(str(file_path))

            # Media turini aniqlash va yuborish
            if file_info["type"] == "video":
                await message.reply_video(
                    video=file_input,
                    caption=f"📹 Video\n🔗 Via @{message.bot.username if hasattr(message.bot, 'username') else ''}"
                )
            elif file_info["type"] == "image":
                await message.reply_photo(
                    photo=file_input,
                    caption=f"🖼 Rasm\n🔗 Via @{message.bot.username if hasattr(message.bot, 'username') else ''}"
                )
            else:
                await message.reply_document(
                    document=file_input,
                    caption=f"📄 Media\n🔗 Via @{message.bot.username if hasattr(message.bot, 'username') else ''}"
                )

            # VIDEO FAYLNI O'CHIRMANG! (Instagram music uchun kerak)
            # Instagram videolari uchun faylni saqlab qoling
            if file_info.get("platform") != "instagram":
                try:
                    file_path.unlink()
                except:
                    pass

        except TelegramAPIError as e:
            logger.error(f"Telegram API error: {e}")
            continue
        except Exception as e:
            logger.error(f"Send media error: {e}")
            continue


@group_router.callback_query(F.data.startswith("group_music:"))
async def handle_group_music_callback(callback_query: CallbackQuery):
    """Guruhda music download callback - Instagram uchun tuzatilgan"""
    user_id = int(callback_query.data.split(":")[1])

    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ Faqat xabar yuborgan foydalanuvchi music yuklay oladi", show_alert=True)
        return

    await callback_query.answer("🎵 Musiqa ajratib olinmoqda...")

    session = user_sessions.get(user_id)
    if not session:
        await callback_query.message.reply("❌ Session tugadi. Qaytadan link yuboring.")
        return

    audio_path = None
    try:
        last_download = session[-1]
        url = last_download["url"]
        platform = last_download["platform"]
        files = last_download["files"]

        logger.info(f"Processing music for platform: {platform}")

        audio_path = None

        if platform == "instagram":
            # Instagram uchun: avval mavjud video fayldan audio ajratish
            video_path = None
            for file_info in files:
                if file_info["type"] == "video":
                    video_path = file_info["path"]
                    break

            if video_path and Path(video_path).exists():
                logger.info(f"Using existing video file: {video_path}")
                from app.bot.handlers.instagram_handler import extract_audio_simple
                audio_path = await extract_audio_simple(video_path)
            else:
                # Video fayl yo'q bo'lsa URL dan qayta audio ajratish
                logger.info(f"Video file not found, extracting from URL: {url}")
                from app.bot.handlers.instagram_handler import extract_audio_from_instagram_video_smart
                audio_path = await extract_audio_from_instagram_video_smart(url)

        elif platform == "tiktok":
            from app.bot.handlers.tiktok_handler import extract_audio_from_tiktok_video_smart
            audio_path = await extract_audio_from_tiktok_video_smart(url)

        else:
            # Boshqa platformalar uchun video fayldan audio ajratish
            video_path = None
            for file_info in files:
                if file_info["type"] == "video":
                    video_path = file_info["path"]
                    break

            if video_path and Path(video_path).exists():
                from app.bot.handlers.instagram_handler import extract_audio_simple
                audio_path = await extract_audio_simple(video_path)
            else:
                await callback_query.message.reply(
                    f"❌ {platform.title()} platformasidan musiqa ajratish hozircha ishlamaydi")
                return

        if not audio_path or not Path(audio_path).exists():
            await callback_query.message.reply("❌ Audio ajratib bo'lmadi")
            return

        logger.info(f"Audio extracted successfully: {audio_path}")

        # Shazam orqali musiqa tanib olish
        shazam_hits = await shz.recognise_music_from_audio(audio_path)
        if not shazam_hits:
            await callback_query.message.reply("❌ Musiqa tanib olinmadi")
            return

        track = shazam_hits[0]["track"]
        title, artist = track["title"], track["subtitle"]
        search_query = f"{title} {artist}"

        # YouTube'dan qidiruv
        youtube_hits = await get_controller().search(search_query)
        if not youtube_hits:
            youtube_hits = [
                get_controller().ytdict_to_info(
                    {
                        "title": title,
                        "artist": artist,
                        "duration": 0,
                        "id": track.get("key", ""),
                    }
                )
            ]

        await callback_query.message.reply(
            f"🎵 <b>Topilgan musiqa:</b>\n\n"
            f"🎤 <b>Nomi:</b> {title}\n"
            f"👤 <b>Ijrochi:</b> {artist}",
            parse_mode="HTML",
        )

        # Cache'ga saqlash
        _cache[user_id] = {
            "hits": youtube_hits,
            "timestamp": time.time(),
        }

        # Musiqa ro'yxatini ko'rsatish
        await callback_query.message.reply(
            format_page_text(youtube_hits, 0),
            reply_markup=create_keyboard(user_id, 0, add_video=True),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"Group music recognition error: {e}")
        await callback_query.message.reply(
            f"❌ Musiqa tanib olishda xatolik: {str(e)[:200]}"
        )

    finally:
        # Audio faylni tozalash
        if audio_path and Path(audio_path).exists():
            await atomic_clear(audio_path)

        # Session'ni tozalash
        user_sessions.pop(user_id, None)

        # Instagram video fayllarini tozalash (music extraction dan keyin)
        if session:
            last_download = session[-1]
            if last_download["platform"] == "instagram":
                for file_info in last_download["files"]:
                    if file_info["type"] == "video":
                        try:
                            Path(file_info["path"]).unlink()
                            logger.info(f"Cleaned up Instagram video: {file_info['path']}")
                        except:
                            pass


async def _is_bot_mentioned(message: Message) -> bool:
    """Bot mention qilinganligini tekshirish"""

    try:
        # Reply qilingan xabar bot tomonidan yuborilganmi?
        if message.reply_to_message and message.reply_to_message.from_user.is_bot:
            return True

        # Bot username mention qilinganmi?
        if message.entities:
            bot_info = await message.bot.get_me()
            bot_username = bot_info.username.lower() if bot_info.username else ""

            for entity in message.entities:
                if entity.type == "mention":
                    mention_text = message.text[entity.offset:entity.offset + entity.length].lower()
                    if bot_username and bot_username in mention_text:
                        return True

        return False
    except Exception as e:
        logger.error(f"Bot mention check error: {e}")
        return False


def _should_respond_automatically(message: Message) -> bool:
    """Bot avtomatik javob berishi kerakligini tekshirish"""

    try:
        # Guruh a'zolari soni 50 dan kam bo'lsa avtomatik javob berish
        if hasattr(message.chat, 'member_count') and message.chat.member_count and message.chat.member_count < 50:
            return True
    except:
        pass

    # Xabar matnida bot nomi yoki kalit so'zlar bo'lsa
    if message.text:
        text_lower = message.text.lower()
        keywords = ['bot', 'downloader', 'yukla', 'download', 'link']
        if any(word in text_lower for word in keywords):
            return True

    return False


async def _send_media_files(message: Message, files: list):
    """Media fayllarni yuborish"""
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

    for file_info in files:
        try:
            file_path = Path(file_info["path"])

            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                continue

            # Fayl hajmini tekshirish
            if file_path.stat().st_size > MAX_FILE_SIZE:
                await message.reply(f"❌ Fayl juda katta: {file_path.name}")
                continue

            file_input = FSInputFile(str(file_path))

            # Media turini aniqlash va yuborish
            if file_info["type"] == "video":
                await message.reply_video(
                    video=file_input,
                    caption=f"📹 Video\n🔗 Via @{message.bot.username if hasattr(message.bot, 'username') else ''}"
                )
            elif file_info["type"] == "image":
                await message.reply_photo(
                    photo=file_input,
                    caption=f"🖼 Rasm\n🔗 Via @{message.bot.username if hasattr(message.bot, 'username') else ''}"
                )
            else:
                await message.reply_document(
                    document=file_input,
                    caption=f"📄 Media\n🔗 Via @{message.bot.username if hasattr(message.bot, 'username') else ''}"
                )

            # Faylni o'chirish (ixtiyoriy)
            try:
                file_path.unlink()
            except:
                pass

        except TelegramAPIError as e:
            logger.error(f"Telegram API error: {e}")
            continue
        except Exception as e:
            logger.error(f"Send media error: {e}")
            continue

