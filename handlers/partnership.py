# -*- coding: utf-8 -*-
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import db
from texts import t
from keyboards.common import back_kb
from config import SMM_API_URL, NUMBER_API_URL

router = Router()


def partnership_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_get_api_key"), callback_data="api_get_key")],
        [InlineKeyboardButton(text=t(lang, "btn_guide"), callback_data="menu_guide")],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main_menu")],
    ])


def api_key_kb(lang: str, revealed: bool) -> InlineKeyboardMarkup:
    rows = []
    if not revealed:
        rows.append([InlineKeyboardButton(text=t(lang, "btn_show_api_key"), callback_data="api_reveal_key")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_regenerate_key"), callback_data="api_regen_key")])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="menu_partnership")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mask_key(key: str) -> str:
    if len(key) <= 8:
        return key[:2] + "*" * (len(key) - 2)
    return key[:6] + "*" * (len(key) - 10) + key[-4:]


@router.callback_query(F.data == "menu_partnership")
async def cb_partnership(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"]
    text = t(lang, "partnership_info", smm_url=SMM_API_URL, number_url=NUMBER_API_URL)
    await callback.message.edit_text(text, reply_markup=partnership_kb(lang))
    await callback.answer()


@router.callback_query(F.data == "api_get_key")
async def cb_api_get_key(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"]
    key = await db.get_or_create_api_key(callback.from_user.id)
    text = t(lang, "api_key_hidden", masked=mask_key(key))
    await callback.message.edit_text(text, reply_markup=api_key_kb(lang, revealed=False))
    await callback.answer()


@router.callback_query(F.data == "api_reveal_key")
async def cb_api_reveal_key(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"]
    key = await db.get_or_create_api_key(callback.from_user.id)
    text = t(lang, "api_key_full", key=key)
    await callback.message.edit_text(text, reply_markup=api_key_kb(lang, revealed=True))
    await callback.answer()


@router.callback_query(F.data == "api_regen_key")
async def cb_api_regen_key(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    lang = user["language"]
    key = await db.regenerate_api_key(callback.from_user.id)
    text = t(lang, "api_key_regenerated", key=key)
    await callback.message.edit_text(text, reply_markup=api_key_kb(lang, revealed=True))
    await callback.answer()
