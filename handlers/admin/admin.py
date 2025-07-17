from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


from utils.imports import _
from database.create import DataBase as DB
from utils.config_loader import config

admin = Router()

@admin.callback_query(F.data == "admin_panel")
async def admin_panel_handler(callback: types.CallbackQuery):
    if callback.from_user.id not in config.admins:
        await callback.answer(_("У вас нет доступа!"), show_alert=True)
        return
    
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=_("🛍 Управление товарами"), callback_data="admin_items"))
    kb.add(InlineKeyboardButton(text=_("👤 Профиль пользователя"), callback_data="admin_user_profile"))
    kb.add(InlineKeyboardButton(text=_("🎁 Реф награда"), callback_data="admin_ref_reward"))
    kb.add(InlineKeyboardButton(text=_("📢 Управление ОП"), callback_data="admin_op"))
    kb.add(InlineKeyboardButton(text=_("📢 Рассылка"), callback_data="admin_mailing"))
    kb.add(InlineKeyboardButton(text=_("📊 Статистика"), callback_data="admin_stats"))
    kb.add(InlineKeyboardButton(text=_("🔙 Назад"), callback_data="back_menu"))
    kb.adjust(1)
    
    await callback.message.edit_text(_("<b>🛠 Админ панель</b>"), reply_markup=kb.as_markup())
