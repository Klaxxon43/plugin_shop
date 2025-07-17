from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext, StorageKey
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.state import State, StatesGroup

import uuid
import os

from utils.imports import _, Bot
from utils.db_init import *
from database.create import DataBase
from utils.config_loader import config

from .admin import admin 

class AddItemStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_instruction = State()
    waiting_for_file = State()
    waiting_for_photo = State()

@admin.callback_query(F.data == "admin_items")
async def admin_items_handler(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text=_("➕ Добавить товар"), callback_data="add_item")
    kb.button(text=_("✏️ Редактировать товар"), callback_data="edit_items")
    kb.button(text=_("🗑️ Удалить товар"), callback_data="delete_item")
    kb.button(text=_("🔙 Назад"), callback_data="admin_panel")

    kb.adjust(1)

    await callback.message.edit_text(_("<b>🛍 Управление товарами</b>"), reply_markup=kb.as_markup())

@admin.callback_query(F.data == "add_item")
async def add_item_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddItemStates.waiting_for_name)
    kb=InlineKeyboardBuilder()
    kb.button(text=_("🔙 Отмена"), callback_data="admin_items")
    await callback.message.edit_text(
        _("✏️ Введите название товара:"),
        reply_markup=kb.as_markup()
    )

@admin.message(AddItemStates.waiting_for_name)
async def process_item_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddItemStates.waiting_for_description)
    kb = InlineKeyboardBuilder()
    kb.button(text=_("🔙 Отмена"), callback_data="admin_items")
    await message.answer(
        _("📝 Введите описание товара:"),
        reply_markup=kb.as_markup()
    )

@admin.message(AddItemStates.waiting_for_description)
async def process_item_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddItemStates.waiting_for_price)
    kb = InlineKeyboardBuilder()
    kb.button(text=_("🔙 Отмена"), callback_data="admin_items")
    await message.answer(
        _("💰 Введите цену товара (только число):"),
        reply_markup=kb.as_markup()
    )

@admin.message(AddItemStates.waiting_for_price)
async def process_item_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(AddItemStates.waiting_for_instruction)
        kb = InlineKeyboardBuilder()
        kb.button(text=_("🔙 Отмена"), callback_data="admin_items")
        await message.answer(
            _("📄 Введите инструкцию для товара (или отправьте '-' чтобы пропустить):"),
            reply_markup=kb.as_markup()
        )
    except ValueError:
        await message.answer(_("❌ Неверный формат цены! Введите число:"))

@admin.message(AddItemStates.waiting_for_instruction)
async def process_item_instruction(message: Message, state: FSMContext):
    instruction = message.text if message.text != '-' else None
    await state.update_data(instruction=instruction)
    await state.set_state(AddItemStates.waiting_for_file)
    kb = InlineKeyboardBuilder()
    kb.button(text=_("🔙 Отмена"), callback_data="admin_items")
    await message.answer(
        _("📁 Отправьте файл плагина (архив или исполняемый файл):"),
        reply_markup=kb.as_markup()
    )

@admin.message(AddItemStates.waiting_for_file, F.document)
async def process_item_file(message: Message, state: FSMContext, bot: Bot):
    # Сохраняем файл плагина
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_ext = file.file_path.split('.')[-1]
    file_path = f"plugins/plugin_{uuid.uuid4()}.{file_ext}"
    
    # Создаем директорию если ее нет
    os.makedirs("plugins", exist_ok=True)
    await bot.download_file(file.file_path, file_path)
    
    await state.update_data(file_path=file_path)
    await state.set_state(AddItemStates.waiting_for_photo)
    
    kb = InlineKeyboardBuilder()
    kb.button(text=_("🔙 Отмена"), callback_data="admin_items")
    kb.button(text=_("⏭ Пропустить"), callback_data="skip_photo")
    
    await message.answer(
        _("📸 Отправьте фото для товара (или нажмите 'Пропустить'):"),
        reply_markup=kb.as_markup()
    )

@admin.callback_query(F.data == "skip_photo", AddItemStates.waiting_for_photo)
async def skip_photo(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await db.items.add_item(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        instruction=data.get('instruction'),
        file_path=data['file_path'],
        photo_path=None
    )
    
    await state.clear()
    await callback.message.answer(_("✅ Товар успешно добавлен без фото!"))
    await admin_items_handler(callback)

@admin.message(AddItemStates.waiting_for_photo, F.photo)
async def process_item_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    
    # Сохраняем фото
    photo_id = message.photo[-1].file_id
    photo = await bot.get_file(photo_id)
    photo_ext = photo.file_path.split('.')[-1]
    photo_path = f"photos/photo_{uuid.uuid4()}.{photo_ext}"
    
    # Создаем директорию если ее нет
    os.makedirs("photos", exist_ok=True)
    await bot.download_file(photo.file_path, photo_path)
    
    await db.items.add_item(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        instruction=data.get('instruction'),
        file_path=data['file_path'],
        photo_path=photo_path
    )
    
    await state.clear()
    await message.answer(_("✅ Товар успешно добавлен с фото!"))
    
    # Возвращаем в меню управления товарами
    kb = InlineKeyboardBuilder()
    kb.button(text=_("🛍 К управлению товарами"), callback_data="admin_items")
    await message.answer(
        _("Что дальше?"),
        reply_markup=kb.as_markup()
    )