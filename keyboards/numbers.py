# -*- coding: utf-8 -*-
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import t


def countries_kb(lang: str, countries: list) -> InlineKeyboardMarkup:
    rows = []
    for c in countries[:60]:
        rows.append([InlineKeyboardButton(
            text=f"🌍 {c['name']} — {c['price']:,} so'm".replace(",", " "),
            callback_data=f"num_country_{c['code']}"
        )])
    rows.append([InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="back_main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_sms_kb(lang: str, order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "get_sms_btn"), callback_data=f"num_getsms_{order_id}")],
    ])
