import os
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.enums.chat_action import ChatAction
from aiogram.fsm.context import FSMContext

from app.bot.controller.admin_controller import export_users_to_excel
from app.bot.filters.admin_filter import AdminFilter
from app.bot.handlers.admin import get_last_7_days_statistics
from app.bot.handlers.channel_handler import get_all_channels
from app.bot.handlers.statistics_handler import get_all_statistics
from app.bot.keyboards.admin_keyboards import (
    get_admin_panel_keyboard,
    get_channel_crud_keyboard,
)
from app.bot.keyboards.general_buttons import main_menu_keyboard
from app.bot.models import Channel

main_menu_router = Router()


@main_menu_router.message(AdminFilter(), F.text == "⚙️ Admin Panel")
async def handle_admin_panel(message: Message):
    text = (
        "🛠 <b>Admin Panel</b>\n\n"
        "👋 Welcome, admin!\n"
        "Please choose an action from the menu below to manage the bot and users effectively."
    )

    await message.answer(
        text, reply_markup=get_admin_panel_keyboard(), parse_mode="HTML"
    )


@main_menu_router.message(AdminFilter(), F.text == "📁 Users excel")
async def handle_statistics(message: Message):
    await message.bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_DOCUMENT)
    file_path: str = await export_users_to_excel()
    try:
        file_name = "Users_report.xlsx"

        doc = FSInputFile(path=file_path, filename=file_name)
        caption = (
            "📊 <b>User Export</b>\n\n"
            f"✅ <b>File:</b> <code>{file_name}</code>\n"
            f"🕒 <b>Generated:</b> <code>{datetime.now():%Y-%m-%d %H:%M:%S}</code>"
        )

        await message.answer_document(document=doc, caption=caption, parse_mode="HTML")

    except Exception as err:
        await message.answer(
            f"❌ Failed to generate export:\n<code>{err}</code>", parse_mode="HTML"
        )
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


@main_menu_router.message(AdminFilter(), F.text == "📊 Statistics")
async def handle_last_users(message: Message):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    stats = await get_last_7_days_statistics()
    channels: list[Channel] = await get_all_channels()
    statistics = await get_all_statistics()
    lines = [
        "👥 <b>User Growth & Referral Leaders</b>\n",
        f"📅 Today: <b>{stats['today']}</b> new",
        f"📅 Yesterday: <b>{stats['yesterday']}</b>",
        f"📅 Last 7 days: <b>{stats['last_week']}</b>",
        f"📅 Last month: <b>{stats['last_month']}</b>",
        f"📅 Last year: <b>{stats['last_year']}</b>",
        f"📅 All time: <b>{stats['all_time']}</b>\n",
    ]

    if stats["top_referrers"]:
        lines.append("🔥 <b>Top 10 Referrers</b>:")
        for idx, ref in enumerate(stats["top_referrers"], start=1):
            lines.append(
                f"{idx}. {ref['name']} (<code>{ref['tg_id']}</code>) — {ref['count']} refs"
            )
    if channels:
        lines.append("\n📡 <b>Connected Telegram Channels</b>:")
        for idx, ch in enumerate(channels, start=1):
            status = "🟢 Active" if ch.is_active else "🔴 Inactive"
            lines.append(f"{idx}. <a href='{ch.link}'>{ch.name}</a> — {status}")
    else:
        lines.append("\nNo channels connected.")

    lines.append("\n📊 <b>Usage Statistics</b>:")
    lines.append(f"• Matndan foydalanishlar soni: <b>{statistics['from_text']}</b>")
    lines.append(f"• Ovoizdan foydalanishlar soni: <b>{statistics['from_voice']}</b>")
    lines.append(
        f"• YouTube'dan foydalanishlar soni: <b>{statistics['from_youtube']}</b>"
    )
    lines.append(
        f"• TikTok'dan foydalanishlar soni: <b>{statistics['from_tiktok']}</b>"
    )
    lines.append(f"• Likee'dan foydalanishlar soni: <b>{statistics['from_like']}</b>")
    lines.append(
        f"• Snapchat'dan foydalanishlar soni: <b>{statistics['from_snapchat']}</b>"
    )
    lines.append(
        f"• Instagram'dan foydalanishlar soni: <b>{statistics['from_instagram']}</b>"
    )
    lines.append(
        f"• Twitter'dan foydalanishlar soni: <b>{statistics['from_twitter']}</b>"
    )

    await message.answer(
        "\n".join(lines), parse_mode="HTML", disable_web_page_preview=True
    )


@main_menu_router.message(AdminFilter(), F.text == "🔧 Settings")
async def handle_settings(message: Message):
    text = (
        "🔧 <b>Settings</b>\n\n"
        "Here you can adjust the bot's settings, including notification preferences, language options, and more."
    )

    await message.answer(text, parse_mode="HTML")


@main_menu_router.message(AdminFilter(), F.text == "📈 Channels")
async def handle_channels(message: Message):
    text = (
        "📈 <b>Channels</b>\n\n"
        "Here you can manage the channels associated with the bot, including adding, editing, and deleting channels."
    )

    await message.answer(
        text, parse_mode="HTML", reply_markup=get_channel_crud_keyboard()
    )


@main_menu_router.message(AdminFilter(), F.text == "🔙 Back to Admin Panel")
async def cancel_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔙 Broadcast cancelled.", reply_markup=get_admin_panel_keyboard()
    )


@main_menu_router.message(AdminFilter(), F.text == "🔙 Back to Main Menu")
async def handle_back_to_admin_panel(message: Message):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    text = (
        "🔙 <b>Admin Panel</b>\n\n"
        "Welcome back! Please choose the action you’d like to perform:"
    )

    await message.answer(
        text=text, parse_mode="HTML", reply_markup=main_menu_keyboard(message)
    )
