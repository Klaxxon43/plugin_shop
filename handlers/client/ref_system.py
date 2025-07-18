from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.imports import _
from database.create import DataBase
from utils.config_loader import config
from utils.db_init import *

from .menu import router

@router.callback_query(F.data == "ref_system")
async def ref_system_handler(callback: types.CallbackQuery):
    user = await db.users.get_user(callback.from_user.id)
    
    ref_link = f"https://t.me/{(await callback.bot.get_me()).username}?start={user['user_id']}"
    ref_count = await db.users.get_ref_count(user['user_id'])
    ref_income = await db.users.get_ref_income(user['user_id'])
    
    text = _('''
👥 <b>Реферальная система</b>

🔗 <b>Ваша реферальная ссылка:</b>
<code>{ref_link}</code>

📊 <b>Статистика:</b>
👥 Количество рефералов: {ref_count}
💰 Ваш доход с рефералов: {ref_income}₽

💸 <b>Как это работает?</b>
Вы получаете {ref_percent}% от всех покупок ваших рефералов!
Приглашайте друзей и зарабатывайте вместе с нами!
''').format(
        ref_link=ref_link,
        ref_count=ref_count,
        ref_income=ref_income,
        ref_percent=config.ref_percent
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_("🔙 Назад"), callback_data="back_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=kb)