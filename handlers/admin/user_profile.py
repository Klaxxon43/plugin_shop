from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.imports import _, State, StatesGroup, Message
from utils.db_init import db
from .admin import admin 

class UserProfileStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()

@admin.callback_query(F.data == "admin_user_profile")
async def admin_user_profile_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserProfileStates.waiting_for_user_id)
    await callback.message.edit_text(
        _("👤 Введите ID пользователя:"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_("🔙 Назад"), callback_data="admin_panel")]
        ])
    )

@admin.message(UserProfileStates.waiting_for_user_id)
async def process_user_id(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        user = await db.users.get_user(user_id)
        
        if not user:
            await message.answer(_("❌ Пользователь не найден!"))
            return
        
        await state.update_data(user_id=user_id)
        
        # Получаем историю и формируем текст
        history_records = await db.history.get_user_history(user_id, limit=5)
        history_text = _("Нет операций")
        
        if history_records:
            # Предполагаем, что записи возвращаются в формате (id, user_id, amount, comment, date)
            history_lines = []
            for record in history_records:
                # Доступ к полям по индексу (адаптируйте под вашу структуру таблицы)
                amount = record[2]  # Предполагаем, что amount на 3 позиции
                comment = record[3] # comment на 4 позиции
                date = record[4]    # date на 5 позиции
                history_lines.append(f"{date}: {amount}₽ - {comment}")
            
            history_text = "\n".join(history_lines)
        
        text = _('''
👤 <b>Профиль пользователя</b>

🆔 ID: <code>{user_id}</code>
👤 Имя: @{username}
💰 Баланс: {balance}₽
📅 Дата регистрации: {reg_time}
🚫 Статус: {banned_status}

📊 <b>Последние операции:</b>
{history}
''').format(
            user_id=user['user_id'],
            username=user['username'] or "нет",
            balance=user['balance'],
            reg_time=user['reg_time'],
            banned_status=_("Забанен") if user['is_banned'] else _("Активен"),
            history=history_text
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=_("➕ Пополнить баланс"), callback_data="add_balance"),
                InlineKeyboardButton(
                    text=_("🚫 Забанить") if not user['is_banned'] else _("✅ Разбанить"),
                    callback_data="toggle_ban"
                )
            ],
            [InlineKeyboardButton(text=_("🔙 Назад"), callback_data="admin_panel")]
        ])
        
        await message.answer(text, reply_markup=kb)
        
    except ValueError as e:
        await message.answer(_("❌ Неверный формат ID! Введите число:"))
        print(e)

@admin.callback_query(F.data == "add_balance", UserProfileStates.waiting_for_user_id)
async def add_balance_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserProfileStates.waiting_for_amount)
    await callback.message.edit_text(
        _("💰 Введите сумму для пополнения:"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_("🔙 Назад"), callback_data="admin_user_profile")]
        ])
    )

@admin.message(UserProfileStates.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text)
        data = await state.get_data()
        user_id = data['user_id']
        await db.users.update_balance(
            user_id=user_id,
            amount=amount,
            comment=_("Пополнение администратором")
        )
        
        await message.answer(
            _("✅ Баланс успешно пополнен на {amount}₽").format(amount=amount),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=_("👤 К профилю"), callback_data=f"admin_user_profile")]
            ])
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer(_("❌ Неверный формат суммы! Введите число:"))

@admin.callback_query(F.data == "toggle_ban", UserProfileStates.waiting_for_user_id)
async def toggle_ban_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    user = await db.users.get_user(user_id)
    
    if user['is_banned']:
        await db.users.unban_user(user_id)
        text = _("✅ Пользователь разбанен")
    else:
        await db.users.ban_user(user_id)
        text = _("🚫 Пользователь забанен")
    
    await callback.answer(text, show_alert=True)
    await admin_user_profile_handler(callback, state)