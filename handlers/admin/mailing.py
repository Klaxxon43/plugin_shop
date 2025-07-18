from aiogram import types, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import Union, Optional
from utils.imports import *
from utils.db_init import *
from aiogram.filters import StateFilter

from .admin import admin

# Клавиатуры
def confirm_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Да, отправить", callback_data="broadcast_confirm")
    kb.button(text="🖼️ Добавить фото", callback_data="add_photo")
    kb.button(text="📋 Добавить кнопки", callback_data="add_buttons")
    kb.button(text="❌ Отменить", callback_data="back_menu")
    kb.adjust(1, 2)
    return kb.as_markup()

def buttons_confirm_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить кнопки", callback_data="buttons_confirm")
    kb.button(text="✏️ Изменить кнопки", callback_data="edit_buttons")
    kb.button(text="❌ Удалить кнопки", callback_data="no_buttons")
    kb.adjust(1, 2)
    return kb.as_markup()

def back_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔙 Назад", callback_data="back_menu")
    return kb.as_markup()

# Обработчики
@admin.callback_query(F.data == "admin_mailing")
async def start_broadcast(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state("get_text")
    await callback.message.edit_text(
        "📢 Введите текст для рассылки:",
        reply_markup=back_keyboard()
    )

@admin.message(StateFilter("get_text"), F.text)
async def get_broadcast_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer(
        f"📢 Текст рассылки:\n\n{message.text}\n\n"
        "Хотите добавить фото или кнопки?",
        reply_markup=confirm_keyboard()
    )
    await state.set_state("confirm_content")

@admin.message(StateFilter("get_text"), F.photo)
async def get_broadcast_photo_with_text(message: types.Message, state: FSMContext):
    await state.update_data(
        photo=message.photo[-1].file_id,
        text=message.caption if message.caption else ""
    )
    data = await state.get_data()
    await message.answer_photo(
        photo=data["photo"],
        caption=f"📢 Предпросмотр:\n\n{data['text']}\n\n"
               "Хотите добавить кнопки?",
        reply_markup=confirm_keyboard()
    )
    await state.set_state("confirm_content")

@admin.callback_query(StateFilter("confirm_content"), F.data == "add_photo")
async def add_photo_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Отправьте фото для рассылки:",
        reply_markup=back_keyboard()
    )
    await state.set_state("get_photo")

@admin.message(StateFilter("get_photo"), F.photo)
async def get_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    data = await state.get_data()
    await message.answer_photo(
        photo=data["photo"],
        caption=f"📢 Предпросмотр:\n\n{data.get('text', '')}\n\n"
               "Хотите добавить кнопки?",
        reply_markup=confirm_keyboard()
    )
    await state.set_state("confirm_content")

@admin.callback_query(StateFilter("confirm_content"), F.data == "add_buttons")
async def add_buttons_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    # Удаляем предыдущее сообщение с кнопками (если есть)
    try:
        await callback.message.delete()
    except:
        pass
    
    # Отправляем новое сообщение с инструкцией
    await callback.message.answer(
        "Отправьте кнопки в формате:\n"
        "Текст кнопки1 - URL1\n"
        "Текст кнопки2 - URL2\n\n"
        "Пример:\n"
        "Наш сайт - https://example.com\n"
        "Telegram - https://t.me/example",
        reply_markup=back_keyboard()
    )
    await state.set_state("get_buttons")

@admin.message(StateFilter("get_buttons"), F.text)
async def get_buttons(message: types.Message, state: FSMContext):
    buttons = []
    for line in message.text.split('\n'):
        if ' - ' in line:
            text, url = line.split(' - ', 1)
            buttons.append((text.strip(), url.strip()))
    
    if not buttons:
        await message.answer("Неверный формат. Попробуйте еще раз:", reply_markup=back_keyboard())
        return
    
    await state.update_data(buttons=buttons)
    data = await state.get_data()
    
    # Создаем клавиатуру для предпросмотра
    builder = InlineKeyboardBuilder()
    for text, url in buttons:
        builder.button(text=text, url=url)
    builder.adjust(1)
    
    # Отправляем предпросмотр в зависимости от типа контента
    if "photo" in data:
        # Удаляем предыдущее сообщение с фото
        try:
            await message.delete()
        except:
            pass
        
        # Отправляем новое сообщение с фото и кнопками
        await message.answer_photo(
            photo=data["photo"],
            caption=f"📢 Предпросмотр:\n\n{data.get('text', '')}\n\n"
                   "Подтвердите добавление кнопок:",
            reply_markup=buttons_confirm_keyboard()
        )
    else:
        # Для текстового сообщения просто редактируем
        await message.answer(
            f"📢 Предпросмотр:\n\n{data.get('text', '')}\n\n"
            "Подтвердите добавление кнопок:",
            reply_markup=buttons_confirm_keyboard()
        )
    
    await state.set_state("confirm_buttons")

@admin.callback_query(StateFilter("confirm_buttons"), F.data == "buttons_confirm")
async def confirm_buttons(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Кнопки добавлены. Хотите начать рассылку?",
        reply_markup=confirm_keyboard()
    )
    await state.set_state("confirm_content")

@admin.callback_query(StateFilter("confirm_buttons"), F.data == "no_buttons")
async def no_buttons(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(buttons=None)
    await callback.message.edit_text(
        "Кнопки не добавлены. Хотите начать рассылку?",
        reply_markup=confirm_keyboard()
    )
    await state.set_state("confirm_content")

@admin.callback_query(StateFilter("confirm_content"), F.data == "broadcast_confirm")
async def start_broadcasting(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    
    # Подготовка клавиатуры
    builder = InlineKeyboardBuilder()
    if "buttons" in data and data["buttons"]:
        for text, url in data["buttons"]:
            builder.button(text=text, url=url)
        builder.adjust(1)
    builder.row(types.InlineKeyboardButton(text="🔙 Назад", callback_data="back_menu"))
    
    # Получаем пользователей
    async with db.con.cursor() as cur:
        await cur.execute("SELECT user_id FROM users WHERE is_banned = FALSE")
        users = await cur.fetchall()
    
    success = 0
    errors = 0
    status_msg = await callback.message.answer("⏳ Начинаем рассылку...")
    
    for (user_id,) in users:
        try:
            if "photo" in data:
                await bot.send_photo(
                    chat_id=user_id,
                    photo=data["photo"],
                    caption=data.get("text", ""),
                    reply_markup=builder.as_markup()
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=data.get("text", "📢 Рассылка"),
                    reply_markup=builder.as_markup()
                )
            success += 1
            await asyncio.sleep(0.1)  # Задержка между отправками
            
        except Exception as e:
            errors += 1
            print(f"Ошибка отправки для {user_id}: {str(e)}")
    
    await status_msg.edit_text(
        f"✅ Рассылка завершена\n\n"
        f"▪️ Успешно: {success}\n"
        f"▪️ Ошибок: {errors}",
        reply_markup=back_keyboard()
    )
    await state.clear()