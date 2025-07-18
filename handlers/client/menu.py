from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.imports import *
from utils.imports import _
from utils.db_init import *
from database.create import DataBase as DB
from utils.config_loader import config

router = Router()

@router.callback_query(F.data == "back_menu")
async def back_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    is_admin = user_id in admins_list
    
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=_("🧩 Плагины"), callback_data="plugins"))
    kb.add(InlineKeyboardButton(text=_("🎩 Профиль"), callback_data="profile"))
    kb.add(InlineKeyboardButton(text=_("👥 Реф система"), callback_data="ref_system"))
    kb.add(InlineKeyboardButton(text=_("ℹ️ О нас"), callback_data="about"))
    
    if is_admin:
        kb.add(InlineKeyboardButton(text=_("🛠 АДМИНКА"), callback_data="admin_panel"))

    kb.adjust(2, 1, 1, 1)

    try:
        await callback.message.edit_text(
            _("<b>Главное меню</b>"),
            reply_markup=kb.as_markup()
        )
    except:
        await callback.message.delete()
        await callback.message.edit_text(
            _("<b>Главное меню</b>"),
            reply_markup=kb.as_markup()
        )

@router.callback_query(F.data == "profile")
async def profile_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await db.users.get_user(user_id)
    
    if not user:
        await callback.answer(_("Пользователь не найден!"), show_alert=True)
        return
    
    balance = user['balance'] or 0
    rub_balance = user['rub_balance'] or 0
    
    text = _('''
👀 <b>Профиль:</b>
                                                  
🪪 <b>ID:</b> <code>{user_id}</code>
💰 <b>Баланс:</b> <code>{balance:.2f}</code>
    ''').format(
        premium_status=_("Есть") if callback.from_user.is_premium else _("Нету"),
        reg_time=user['reg_time'],
        user_id=user_id,
        balance=balance,
        rub_balance=rub_balance
    )
    
    await callback.message.edit_text(text, reply_markup=profile_kb())

def profile_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text=_("🔙 Назад"), callback_data="back_menu")
    return kb.as_markup()









