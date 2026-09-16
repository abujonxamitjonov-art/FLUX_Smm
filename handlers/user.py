# -*- coding: utf-8 -*-
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from database import db
from texts import t
from states import Registration
from keyboards.common import (
    language_kb, contact_kb, subscribe_kb, main_menu_kb, remove_kb,
)
from config import ADMIN_ID

router = Router()


async def check_subscriptions(bot: Bot, user_id: int) -> bool:
    channels = await db.get_mandatory_channels()
    if not channels:
        return True
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch["chat_id"], user_id)
            if member.status in ("left", "kicked"):
                return False
        except Exception:
            continue  # bot admin bo'lmasa yoki xatolik bo'lsa o'tkazib yuboramiz
    return True


async def show_main_menu(message_or_cb, lang: str, edit: bool = False):
    text = t(lang, "main_menu")
    kb = main_menu_kb(lang)
    if edit and isinstance(message_or_cb, CallbackQuery):
        try:
            await message_or_cb.message.edit_text(text, reply_markup=kb)
        except Exception:
            await message_or_cb.message.answer(text, reply_markup=kb)
    else:
        target = message_or_cb.message if isinstance(message_or_cb, CallbackQuery) else message_or_cb
        await target.answer(text, reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, command: CommandObject):
    user_id = message.from_user.id

    if await db.is_currently_blocked(user_id):
        user = await db.get_user(user_id)
        lang = user["language"] if user else "uz"
        await message.answer(t(lang, "blocked"))
        return

    referrer_id = None
    if command.args and command.args.startswith("ref_"):
        ref_code = command.args.replace("ref_", "")
        ref_user = await db.get_user_by_referral_code(ref_code)
        if ref_user and ref_user["user_id"] != user_id:
            referrer_id = ref_user["user_id"]

    user = await db.get_user(user_id)
    if user is None:
        await db.create_user_if_not_exists(
            user_id, message.from_user.username or "", message.from_user.full_name, referrer_id
        )
        await state.set_state(Registration.choosing_language)
        await message.answer(t("uz", "choose_language"), reply_markup=language_kb())
        return

    if not user["language"] or user["registered"] == 0:
        if not user["language"]:
            await state.set_state(Registration.choosing_language)
            await message.answer(t("uz", "choose_language"), reply_markup=language_kb())
            return
        lang = user["language"]
        await state.set_state(Registration.waiting_contact)
        await message.answer(t(lang, "share_contact"), reply_markup=contact_kb(lang))
        return

    lang = user["language"]
    if not await check_subscriptions(message.bot, user_id):
        channels = await db.get_mandatory_channels()
        await message.answer(t(lang, "subscribe_required"), reply_markup=subscribe_kb(channels, lang))
        return

    await state.clear()
    await show_main_menu(message, lang)


@router.callback_query(F.data.startswith("lang_"))
async def cb_choose_language(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await db.set_user_language(callback.from_user.id, lang)
    await callback.message.edit_text(t(lang, "language_set"))
    await state.set_state(Registration.waiting_contact)
    await callback.message.answer(t(lang, "share_contact"), reply_markup=contact_kb(lang))
    await callback.answer()


@router.message(Registration.waiting_contact, F.contact)
async def process_contact(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if message.contact.user_id != user_id:
        user = await db.get_user(user_id)
        lang = user["language"] if user else "uz"
        await message.answer(t(lang, "contact_wrong"))
        return

    await db.set_user_phone_and_register(user_id, message.contact.phone_number)
    user = await db.get_user(user_id)
    lang = user["language"]

    await message.answer(t(lang, "registered"), reply_markup=remove_kb())
    await state.clear()

    if not await check_subscriptions(message.bot, user_id):
        channels = await db.get_mandatory_channels()
        await message.answer(t(lang, "subscribe_required"), reply_markup=subscribe_kb(channels, lang))
        return

    await show_main_menu(message, lang)


@router.message(Registration.waiting_contact)
async def process_contact_wrong(message: Message):
    user = await db.get_user(message.from_user.id)
    lang = user["language"] if user else "uz"
    await message.answer(t(lang, "contact_wrong"))


@router.callback_query(F.data == "check_subs")
async def cb_check_subs(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    if await check_subscriptions(callback.bot, callback.from_user.id):
        await callback.message.delete()
        await show_main_menu(callback, lang)
    else:
        await callback.answer(t(lang, "subscribe_not_done"), show_alert=True)


@router.callback_query(F.data == "back_main_menu")
async def cb_back_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = await db.get_user(callback.from_user.id)
    lang = user["language"] if user else "uz"
    await show_main_menu(callback, lang, edit=True)
    await callback.answer()


@router.callback_query(F.data == "menu_balance")
async def cb_balance(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"]
    text = t(lang, "balance_info", user_id=user["user_id"], balance=f"{user['balance']:,}".replace(",", " "))
    from keyboards.common import back_kb
    await callback.message.edit_text(text, reply_markup=back_kb(lang, "back_main_menu"))
    await callback.answer()


@router.callback_query(F.data == "menu_guide")
async def cb_guide(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"]
    from keyboards.common import back_kb
    await callback.message.edit_text(t(lang, "guide_text"), reply_markup=back_kb(lang, "back_main_menu"))
    await callback.answer()


@router.callback_query(F.data == "menu_support")
async def cb_support(callback: CallbackQuery):
    from config import ADMIN_USERNAME
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    user = await db.get_user(callback.from_user.id)
    lang = user["language"]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "contact_admin_btn"), url=f"https://t.me/{ADMIN_USERNAME}")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main_menu")],
    ])
    await callback.message.edit_text(t(lang, "support_text"), reply_markup=kb)
    await callback.answer()
