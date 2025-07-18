from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.state import StateFilter
from aiogram.fsm.state import StatesGroup, State
from utils.imports import _ 
from database.create import DataBase
from utils.db_init import db
from aiogram import Bot

from .admin import admin 

@admin.callback_query(F.data == "admin_op")
async def admin_op_handler(callback: types.CallbackQuery, bot: Bot):
    try:
        op_channels = await db.op.get_op_channels()
        
        kb = InlineKeyboardBuilder()
        
        for channel in op_channels:
            try:
                # Проверяем что channel содержит нужные ключи
                if not all(key in channel for key in ['id', 'channel_id']):
                    continue
                    
                chat = await bot.get_chat(channel['channel_id'])
                button_text = f"Канал: {chat.title}" if hasattr(chat, 'title') else f"Чат ID: {chat.id}"
                kb.add(InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"edit_op_{channel['id']}"
                ))
            except Exception as e:
                print(f"Ошибка при обработке канала: {e}")
                kb.add(InlineKeyboardButton(
                    text=f"Канал ID: {channel['id']}",
                    callback_data=f"edit_op_{channel['id']}"
                ))
        
        kb.add(InlineKeyboardButton(
            text="➕ Добавить ОП",
            callback_data="add_op"
        ))
        
        kb.add(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="admin_panel"
        ))
        
        kb.adjust(1)
        
        await callback.message.edit_text(
            "📢 Управление ОП каналами\n\nВыберите канал:",
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        print(f"Ошибка в admin_op_handler: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@admin.callback_query(F.data.startswith("edit_op_"))
async def edit_op_handler(callback: types.CallbackQuery, bot: Bot):
    try:
        # Безопасное извлечение ID
        parts = callback.data.split('_')
        if len(parts) < 3:
            raise ValueError("Некорректный формат callback_data")
            
        channel_id = int(parts[2])
        channel = await get_channel_by_id(channel_id)
        
        if not channel:
            await callback.answer("Канал не найден", show_alert=True)
            return
            
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(
            text="✏️ Изменить ссылку",
            callback_data=f"change_op_url_{channel_id}"
        ))
        kb.add(InlineKeyboardButton(
            text="❌ Удалить канал",
            callback_data=f"delete_op_{channel_id}"
        ))
        kb.add(InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="admin_op"
        ))
        kb.adjust(1)
        chat = await bot.get_chat(channel['channel_id'])
        await callback.message.edit_text(
            f"<b>🛠 Редактирование канала</b>\n\n<b>ID:</b> <code>{channel['id']}</code>\n<b>Ссылка:</b> <code>@{chat.username}</code>",
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        print(f"Ошибка в edit_op_handler: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@admin.callback_query(F.data.startswith("delete_op_"))
async def delete_op_handler(callback: types.CallbackQuery):
    try:
        parts = callback.data.split('_')
        if len(parts) < 3:
            raise ValueError("Некорректный формат callback_data")
            
        channel_id = int(parts[2])
        
        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"confirm_delete_op_{channel_id}"
        ))
        kb.add(InlineKeyboardButton(
            text="❌ Нет, отмена",
            callback_data=f"edit_op_{channel_id}"
        ))
        
        await callback.message.edit_text(
            "⚠️ Вы уверены что хотите удалить этот канал?",
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        print(f"Ошибка в delete_op_handler: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@admin.callback_query(F.data.startswith("confirm_delete_op_"))
async def confirm_delete_op_handler(callback: types.CallbackQuery, bot: Bot):
    try:
        parts = callback.data.split('_')
        if len(parts) < 4:
            raise ValueError("Некорректный формат callback_data")
            
        channel_id = int(parts[3])
        channel = await get_channel_by_id(channel_id)
        
        if not channel:
            await callback.answer("Канал не найден", show_alert=True)
            return
            
        await db.op.remove_op_channel(channel['channel_id'])
        await callback.answer("✅ Канал удален!", show_alert=True)
        await admin_op_handler(callback, bot)
    except Exception as e:
        print(f"Ошибка в confirm_delete_op_handler: {e}")
        await callback.answer("Произошла ошибка при удалении", show_alert=True)

async def get_channel_by_id(channel_id: int):
    try:
        op_channels = await db.op.get_op_channels()
        for channel in op_channels:
            if isinstance(channel, dict) and channel.get('id') == channel_id:
                return channel
        return None
    except Exception as e:
        print(f"Ошибка в get_channel_by_id: {e}")
        return None
    
from aiogram.fsm.state import StatesGroup, State

class ChangeOpStates(StatesGroup):
    waiting_for_url = State()

@admin.callback_query(F.data.startswith("change_op_url_"))
async def change_op_url_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        parts = callback.data.split('_')
        if len(parts) < 4:
            await callback.answer("Некорректный формат данных", show_alert=True)
            return

        channel_id = int(parts[3])
        channel = await get_channel_by_id(channel_id)

        if not channel:
            await callback.answer("Канал не найден", show_alert=True)
            return

        await state.set_state(ChangeOpStates.waiting_for_url)
        await state.update_data(channel_id=channel_id, old_url=channel['channel_id'])

        kb = InlineKeyboardBuilder()
        kb.add(InlineKeyboardButton(text="🔙 Отмена", callback_data=f"edit_op_{channel_id}"))
        
        await callback.message.edit_text(
            "🔗 Введите новую ссылку на канал (например @channelname или https://t.me/channelname):",
            reply_markup=kb.as_markup()
        )
    except Exception as e:
        print(f"Ошибка в change_op_url_handler: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

@admin.message(ChangeOpStates.waiting_for_url)
async def process_new_op_url(message: types.Message, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        channel_id = data.get("channel_id")
        old_url = data.get("old_url")
        input_text = message.text.strip()

        # Извлекаем username или ID из разных форматов ссылок
        if input_text.startswith("https://t.me/"):
            channel_ref = input_text.split("https://t.me/")[1].split("/")[0]
        elif input_text.startswith("@"):
            channel_ref = input_text[1:]
        else:
            channel_ref = input_text.lstrip("@")

        # Получаем полную информацию о канале
        try:
            chat = await bot.get_chat(f"@{channel_ref}" if not channel_ref.lstrip("-").isdigit() else channel_ref)
            new_channel_id = str(chat.id)
            
            # Проверяем что бот админ в канале
            try:
                bot_member = await bot.get_chat_member(chat.id, bot.id)
                if bot_member.status not in ['administrator', 'creator']:
                    await message.answer("❌ Бот не является администратором этого канала")
                    return
            except Exception as e:
                print(f"Ошибка проверки прав бота: {e}")
                await message.answer("❌ Не удалось проверить права бота в канале")
                return

            # Обновляем в БД (сохраняем ID канала)
            await db.op.update_channel_url(channel_id, new_channel_id)
            kb = InlineKeyboardBuilder() 
            kb.button(text='Назад', callback_data=f'edit_op_{new_channel_id}')
            
            await message.answer(f"✅ Канал успешно обновлен!\n"
                               f"Новый ID: <code>{new_channel_id}</code>\n"
                               f"Username: @{chat.username}" if chat.username else f"ID: {chat.id}", reply_markup=kb.as_markup())
            
        except Exception as e:
            print(f"Ошибка получения информации о канале: {e}")
            await message.answer("❌ Не удалось получить информацию о канале. Проверьте ссылку и права бота.")

        await state.clear()
        
    except Exception as e:
        print(f"Ошибка в process_new_op_url: {e}")
        await message.answer("❌ Произошла ошибка при обновлении ссылки")
        await state.clear()


@admin.callback_query(F.data == "add_op")
async def add_op_handler(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("waiting_for_op_url")
    await callback.message.edit_text(
        _("📝 <b>Добавление нового ОП канала</b>\n\n"
          "Отправьте мне ссылку на канал в формате:\n"
          "<code>@username</code> или <code>https://t.me/username</code>\n\n"
          "❕ Бот должен быть админом в этом канале!"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_op")
        ]])
    )

# Обработчик для состояния добавления ОП
@admin.message(F.text, StateFilter("waiting_for_op_url"))
async def process_op_url(message: types.Message, state: FSMContext, bot: Bot):
    url = message.text.strip()
    
    # Извлекаем username или ID канала из ссылки
    if url.startswith("https://t.me/"):
        channel_id = url.split("https://t.me/")[1].split("/")[0]
    elif url.startswith("@"):
        channel_id = url[1:]
    else:
        channel_id = url

    try:
        chat = await bot.get_chat(f"@{channel_id}")
        channel_username = channel_id
        channel_id = chat.id
    except:
        await message.answer("❌ Некорректный формат ссылки. Попробуйте еще раз.")
        return
    
    # Добавляем канал в БД
    await db.op.add_op_channel(channel_id) 
    await state.clear()
    
    await message.answer(f"✅ ОП канал @{channel_username} успешно добавлен!")

# Вспомогательная функция для получения канала по ID
async def get_channel_by_id(channel_id: int):
    op_channels = await db.op.get_op_channels()
    for channel in op_channels:
        if channel['id'] == channel_id:
            return channel
    return None