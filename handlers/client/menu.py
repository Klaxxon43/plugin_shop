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
    await callback.answer()
    await state.clear()
    user_id = callback.from_user.id
    
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=_("🧩 Плагины"), callback_data="plugins"))
    kb.add(InlineKeyboardButton(text=_("👥 Реф система"), callback_data="ref_system"))
    kb.add(InlineKeyboardButton(text=_("ℹ️ О нас"), callback_data="about"))
    
    if user_id in config.admins:
        kb.add(InlineKeyboardButton(text=_("🛠 АДМИНКА"), callback_data="admin_panel"))
    kb.adjust(1)

    await callback.message.edit_text(
        _("<b>Главное меню</b>"),
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "profile")
async def profile_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    
    if not user:
        await callback.answer(_("Пользователь не найден!"), show_alert=True)
        return
    
    balance = user['balance'] or 0
    rub_balance = user['rub_balance'] or 0
    
    text = _('''
👀 <b>Профиль:</b>
                                     
⭐️ <b>TG Premium:</b> {premium_status}
📅 <b>Дата регистрации:</b> <em>{reg_time}</em>                                     
🪪 <b>ID:</b> <code>{user_id}</code>

💰 Баланс $MICO: {balance:.2f} MitCoin
💳 Баланс руб: {rub_balance:.2f} ₽
    ''').format(
        premium_status=_("Есть") if callback.from_user.is_premium else _("Нету"),
        reg_time=user['reg_time'],
        user_id=user_id,
        balance=balance,
        rub_balance=rub_balance
    )
    
    await callback.message.edit_text(text, reply_markup=profile_kb())

def profile_kb():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(text=_("🔙 Назад"), callback_data="back_menu"))
    return kb











@router.message(Command("language"))
async def language_command(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en")
    )
    
    await message.answer(
        _("Выберите язык / Choose language:"),
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("set_lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[-1]
    
    # Обновляем язык в базе данных
    await db.users.update_user(
        user_id=callback.from_user.id,
        language=lang
    )
    
    # Форсируем установку языка для текущего сообщения
    i18n.ctx_locale.set(lang)
    
    # Отправляем подтверждение на выбранном языке
    if lang == "en":
        response = "Language changed to English 🇬🇧"
    else:
        response = "Язык изменен на русский 🇷🇺"
    
    await callback.message.edit_text(response)
    await callback.answer()