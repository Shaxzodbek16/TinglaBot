from aiogram import Router, F

from aiogram.filters import Command
from aiogram.utils.i18n import gettext as _

from app.bot.filters.admin_filter import AdminFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from app.bot.handlers.admin import update_premium_price
from app.bot.keyboards.admin_keyboards import get_admin_panel_keyboard
from app.bot.state.payment import FillBalanceStates, UnFillBalanceStates
from aiogram.fsm.context import FSMContext
from app.bot.handlers.user_handlers import (
    get_user_by_tg_id,
    add_user_balance,
    remove_user_balance,
)

router = Router()


@router.message(Command("payment"))
async def payment_handler(message: Message):
    await message.answer(
        _("payment_info").format(username="@tmshaxzodbek"),
    )


@router.message(Command("balance"))
async def balance_handler(message: Message):
    user = await get_user_by_tg_id(message.from_user.id)
    if not user:
        return await message.answer(_("You are not registered in the system ❌"))

    balance = user.balance
    if balance is None:
        balance = 0.0

    await message.answer(
        _("Your current balance is: {balance} 💰").format(balance=balance)
    )
    return None


# --- Start Flow ---
@router.message(AdminFilter(), F.text == "💲 Fill Balance")
async def fill_balance_handler(message: Message, state: FSMContext):
    await message.answer(_("Please send the user's Telegram ID 👤"))
    await state.set_state(FillBalanceStates.waiting_for_tg_id)


# --- Get User's Telegram ID ---
@router.message(AdminFilter(), FillBalanceStates.waiting_for_tg_id)
async def process_tg_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        user = await get_user_by_tg_id(message.from_user.id)
        if not user:
            await state.clear()
            return await message.answer(_("User not found ❌"))
        return await message.answer(_("Invalid Telegram ID. Please send only numbers."))

    await state.update_data(tg_id=int(message.text))
    await message.answer(_("How much do you want to add to the balance? 💵"))
    await state.set_state(FillBalanceStates.waiting_for_amount)
    return None


# --- Get Amount and Update Balance ---
@router.message(AdminFilter(), FillBalanceStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError()
    except ValueError:
        return await message.answer(_("Please send a valid positive number 💸"))

    data = await state.get_data()
    tg_id = data["tg_id"]

    user = await get_user_by_tg_id(tg_id)
    if not user:
        await state.clear()
        return await message.answer(_("User not found ❌"))

    await add_user_balance(tg_id, amount)
    await message.answer(
        _("Successfully added {amount} to user {tg_id} ✅").format(
            amount=amount, tg_id=tg_id
        )
    )
    await state.clear()
    return None


@router.message(AdminFilter(), F.text == "Remove from balance")
async def remove_balance_handler(message: Message, state: FSMContext):
    await message.answer(_("Please send the user's Telegram ID 👤"))
    await state.set_state(UnFillBalanceStates.waiting_for_tg_id)


@router.message(AdminFilter(), UnFillBalanceStates.waiting_for_tg_id)
async def process_remove_tg_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer(_("Invalid Telegram ID. Please send only numbers."))

    await state.update_data(tg_id=int(message.text))
    await message.answer(_("How much do you want to remove from the balance? 💵"))
    await state.set_state(UnFillBalanceStates.waiting_for_amount)
    return None


@router.message(AdminFilter(), UnFillBalanceStates.waiting_for_amount)
async def process_remove_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError()
    except ValueError:
        return await message.answer(_("Please send a valid positive number 💸"))

    data = await state.get_data()
    tg_id = data["tg_id"]
    user = await get_user_by_tg_id(tg_id)
    if not user:
        await state.clear()
        return await message.answer(_("User not found ❌"))
    try:
        await remove_user_balance(tg_id, amount)
        await message.answer(
            _("Successfully removed {amount} from user {tg_id} ✅").format(
                amount=amount, tg_id=tg_id
            )
        )
    except ValueError:
        await state.clear()
        return await message.answer(_("Insufficient balance to remove this amount ❌"))


class PriceForm(StatesGroup):
    waiting_for_price = State()


@router.message(AdminFilter(), F.text == "Update Premium price")
async def ask_new_price_value(message: Message, state: FSMContext):
    await state.set_state(PriceForm.waiting_for_price)
    await message.answer(
        text="✍️ Please send the new integer value (must be > 0), or tap 🔙 to cancel:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Back to Admin Panel")]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


@router.message(AdminFilter(), F.text == "🔙 Back to Admin Panel", ~F.state)
async def back_from_menu(message: Message, state: FSMContext):
    await message.answer(
        "🔙 Returning to Admin Panel.", reply_markup=get_admin_panel_keyboard()
    )


@router.message(
    AdminFilter(), PriceForm.waiting_for_price, F.text == "🔙 Back to Admin Panel"
)
async def cancel_update(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🔙 Update cancelled. Here’s the Admin Panel:",
        reply_markup=get_admin_panel_keyboard(),
    )


@router.message(AdminFilter(), PriceForm.waiting_for_price)
async def process_new_price_value(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        val = float(text)
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

    await update_premium_price(val)
    await state.clear()
    await message.answer(
        text=f"✅ Tokens per referral updated to <b>{val}</b>.",
        parse_mode="HTML",
        reply_markup=get_admin_panel_keyboard(),
    )
