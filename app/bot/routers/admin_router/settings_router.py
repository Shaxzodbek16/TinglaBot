from aiogram import Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ContentType,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.bot.filters.admin_filter import AdminFilter
from app.bot.handlers.admin import (
    get_token_per_referral,
    update_token_per_referral,
    run_broadcast,
)
from app.bot.keyboards.admin_keyboards import (
    get_admin_panel_keyboard,
    settings_keyboard,
    ask_media_kb,
    back_to_admin_kb,
)
from app.bot.state.settings_state import BroadcastForm

settings_router = Router()


class SettingsForm(StatesGroup):
    waiting_for_token = State()


@settings_router.message(AdminFilter(), F.text == "🔧 Settings")
async def open_settings(message: Message, state: FSMContext):
    await state.clear()
    current = await get_token_per_referral()
    await message.answer(
        text=(
            "⚙️ <b>Settings</b>\n\n" f"🔢 Current tokens per referral: <b>{current}</b>"
        ),
        parse_mode="HTML",
        reply_markup=settings_keyboard(),
    )


# 2️⃣ Admin taps “Update Tokens per Referral”
@settings_router.message(AdminFilter(), F.text == "Update Tokens per Referral")
async def ask_new_token_value(message: Message, state: FSMContext):
    await state.set_state(SettingsForm.waiting_for_token)
    await message.answer(
        text="✍️ Please send the new integer value (must be > 0), or tap 🔙 to cancel:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Back to Admin Panel")]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


@settings_router.message(AdminFilter(), F.text == "🔙 Back to Admin Panel", ~F.state)
async def back_from_menu(message: Message, state: FSMContext):
    await message.answer(
        "🔙 Returning to Admin Panel.", reply_markup=get_admin_panel_keyboard()
    )


@settings_router.message(
    AdminFilter(), SettingsForm.waiting_for_token, F.text == "🔙 Back to Admin Panel"
)
async def cancel_update(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔙 Update cancelled. Here’s the Admin Panel:",
        reply_markup=get_admin_panel_keyboard(),
    )


@settings_router.message(AdminFilter(), SettingsForm.waiting_for_token)
async def process_new_token_value(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        val = int(text)
        if val <= 0:
            raise ValueError()
    except ValueError:
        await message.answer(
            "⚠️ Invalid input. Send a positive integer or tap 🔙 Back to Admin Panel.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🔙 Back to Admin Panel")]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
        return

    await update_token_per_referral(val)
    await state.clear()
    await message.answer(
        text=f"✅ Tokens per referral updated to <b>{val}</b>.",
        parse_mode="HTML",
        reply_markup=get_admin_panel_keyboard(),
    )


# send messages
@settings_router.message(AdminFilter(), F.text == "Send Message to All Users")
async def start_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "📢 <b>Broadcast to All Users</b>\n\n"
        "Send me the message text in <i>HTML</i> format:",
        parse_mode="HTML",
        reply_markup=back_to_admin_kb,
    )
    await state.set_state(BroadcastForm.waiting_for_text)


@settings_router.message(AdminFilter(), BroadcastForm.waiting_for_text)
async def process_broadcast_text(message: Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer(
        "🎞 Would you like to include a photo/video/document?", reply_markup=ask_media_kb
    )
    await state.set_state(BroadcastForm.waiting_for_media)


# 5️⃣ Skip media → kick off broadcast
@settings_router.message(
    AdminFilter(), BroadcastForm.waiting_for_media, F.text == "⏭ Skip Media"
)
async def skip_broadcast_media(message: Message, state: FSMContext):
    data = await state.get_data()
    await run_broadcast(text=data["text"], media=None, admin_id=message.chat.id)
    await message.answer(
        "✅ Broadcast started in background.\n"
        "You’ll get no flood, and I’ll ping you when it’s done.",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="HTML",
    )
    await state.clear()


# 6️⃣ Admin wants to add media
@settings_router.message(
    AdminFilter(),
    BroadcastForm.waiting_for_media,
    F.content_type.in_([ContentType.PHOTO, ContentType.VIDEO, ContentType.DOCUMENT]),
)
async def process_broadcast_media(message: Message, state: FSMContext):
    media = None
    if message.photo:
        media = message.photo[-1].file_id
        ctype = ContentType.PHOTO
    elif message.video:
        media = message.video.file_id
        ctype = ContentType.VIDEO
    else:
        media = message.document.file_id
        ctype = ContentType.DOCUMENT

    data = await state.get_data()
    await run_broadcast(
        text=data["text"], media=(ctype, media), admin_id=message.chat.id
    )

    await message.answer(
        "✅ Broadcast with media started in background.",
        reply_markup=get_admin_panel_keyboard(),
        parse_mode="HTML",
    )
    await state.clear()
