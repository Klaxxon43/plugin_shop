from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext, StorageKey
from aiogram.types import InlineKeyboardButton, Message, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.state import State, StatesGroup

import uuid
import os
from datetime import datetime

from utils.imports import _, Bot, logger
from utils.db_init import *
from database.create import DataBase
from utils.config_loader import config

from .admin import admin 

class AddItemStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_category = State()
    waiting_for_instruction = State()
    waiting_for_file = State()
    waiting_for_photo = State()

@admin.callback_query(F.data == "admin_items")
async def admin_items_handler(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text=_("➕ Добавить товар"), callback_data="add_item")
    kb.button(text=_("✏️ Редактировать товар"), callback_data="edit_items")
    kb.button(text=_("🔙 Назад"), callback_data="admin_panel")
    kb.adjust(1)

    try:
        # First try to edit the message
        await callback.message.edit_text(_("<b>🛍 Управление товарами</b>"), reply_markup=kb.as_markup())
    except:
        try:
            # If editing fails, try to delete the original message
            await callback.message.delete()
        except:
            pass  # If deletion also fails, just ignore
        # Then send a new message
        await callback.message.answer(_("<b>🛍 Управление товарами</b>"), reply_markup=kb.as_markup())

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

# @admin.message(AddItemStates.waiting_for_price)
# async def process_item_price(message: Message, state: FSMContext):
#     try:
#         price = float(message.text)
#         if price <= 0:
#             raise ValueError
#         await state.update_data(price=price)
#         await state.set_state(AddItemStates.waiting_for_category)
#         kb = InlineKeyboardBuilder()
#         kb.button(text=_("🔙 Отмена"), callback_data="admin_items")
#         await message.answer(
#             _("📂 Введите категорию товара (например: 'Плагины', 'Скрипты'):"),
#             reply_markup=kb.as_markup()
#         )
#     except ValueError:
#         await message.answer(_("❌ Неверный формат цены! Введите положительное число:"))

@admin.message(AddItemStates.waiting_for_price)
async def process_item_category(message: Message, state: FSMContext):
    price = float(message.text)
    if price <= 0:
        raise ValueError
    await state.update_data(price=price)
    await state.set_state(AddItemStates.waiting_for_instruction)
    kb = InlineKeyboardBuilder()
    kb.button(text=_("🔙 Отмена"), callback_data="admin_items")
    await message.answer(
        _("📄 Введите инструкцию для товара (или отправьте '-' чтобы пропустить):"),
        reply_markup=kb.as_markup()
    )

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

async def process_purchase_with_referral(user_id: int, amount: float, item_id: int, bot: Bot):
    """
    Обработка покупки с учетом реферальной системы
    :param user_id: ID покупателя
    :param amount: Сумма покупки
    :param item_id: ID товара
    :param bot: Экземпляр бота для отправки уведомлений
    """
    # 1. Получаем реферера
    referrer_id = await db.users.get_referrer(user_id)
    
    if referrer_id:
        # 2. Рассчитываем бонус (15% от суммы)
        ref_bonus = round(amount * (float(config.ref_percent) / 100), 2)
        
        # 3. Начисляем бонус рефереру
        await db.users.update_balance(
            referrer_id,
            ref_bonus,
            f"Реферальный бонус за покупку товара {item_id}",
            operation_type="ref_bonus",
            item_id=item_id
        )
        
        # 4. Можно отправить уведомление рефереру
        try:
            await bot.send_message(
                referrer_id,
                _("🎉 Вы получили реферальный бонус {bonus}₽ за покупку вашего реферала!").format(bonus=ref_bonus)
            )
        except:
            pass  # Если не удалось отправить сообщение
    
    # 5. Регистрируем покупку
    await db.items.increment_purchases(item_id)
    await db.history.add_record(
        user_id=user_id,
        amount=-amount,
        comment=f"Покупка товара {item_id}",
        operation_type="purchase",
        item_id=item_id
    )

class EditItemStates(StatesGroup):
    waiting_for_item_select = State()
    waiting_for_new_name = State()
    waiting_for_new_description = State()
    waiting_for_new_price = State()
    waiting_for_new_instruction = State()
    waiting_for_new_file = State()
    waiting_for_new_photo = State()

@admin.callback_query(F.data == "edit_items")
async def edit_items_start(callback: types.CallbackQuery, state: FSMContext):
    # Получаем все товары из базы
    items = await db.items.get_all_items()
    
    if not items:
        await callback.answer(_("Нет товаров для редактирования!"), show_alert=True)
        return
    
    # Создаем клавиатуру с товарами
    kb = InlineKeyboardBuilder()
    for item in items:
        kb.button(
            text=f"{item['name']} ({item['price']}₽)", 
            callback_data=f"edit_item_{item['id']}"
        )
    
    kb.button(text=_("🔙 Назад"), callback_data="admin_items")
    kb.adjust(1)
    
    await callback.message.edit_text(
        _("📝 Выберите товар для редактирования:"),
        reply_markup=kb.as_markup()
    )
    await state.set_state(EditItemStates.waiting_for_item_select)

@admin.callback_query(F.data.startswith("edit_item_"), EditItemStates.waiting_for_item_select)
async def edit_item_selected(callback: types.CallbackQuery, state: FSMContext):
    try:
        # Безопасный парсинг item_id
        parts = callback.data.split("_")
        if len(parts) < 3 or not parts[2].isdigit():
            await callback.answer("Неверный формат данных", show_alert=True)
            return

        item_id = int(parts[2])
        item = await db.items.get_item(item_id)
        if not item:
            await callback.answer("Товар не найден", show_alert=True)
            return

        await state.update_data(item_id=item_id, current_item=item)
        await show_item_edit_menu(callback, item)

    except Exception as e:
        logger.error(f"Ошибка при выборе товара: {e}")
        await callback.answer("Произошла ошибка", show_alert=True)

async def show_item_edit_menu(callback: types.CallbackQuery, item: dict, is_new_message: bool = False):
    text = _('''
📦 <b>Информация о товаре:</b>

🏷 <b>Название:</b> {name}
📝 <b>Описание:</b> {description}
💰 <b>Цена:</b> {price}₽
📄 <b>Инструкция:</b> {instruction}
🔄 <b>Статус:</b> {status}
''').format(
        name=item['name'],
        description=item['description'],
        price=item['price'],
        instruction=item.get('instruction', _("нет")),
        status=_("Активен") if item.get('is_active', True) else _("Неактивен")
    )

    kb = InlineKeyboardBuilder()
    kb.button(text=_("✏️ Изменить название"), callback_data="change_name")
    kb.button(text=_("📝 Изменить описание"), callback_data="change_description")
    kb.button(text=_("💰 Изменить цену"), callback_data="change_price")
    kb.button(text=_("📄 Изменить инструкцию"), callback_data="change_instruction")
    kb.button(text=_("📁 Обновить файл"), callback_data="change_file")
    kb.button(text=_("🖼 Обновить фото"), callback_data="change_photo")
    kb.button(text=_("📥 Выгрузить файл"), callback_data="download_file")
    
    if item.get('is_active', True):
        kb.button(text=_("⛔️ Деактивировать"), callback_data="toggle_active")
    else:
        kb.button(text=_("✅ Активировать"), callback_data="toggle_active")
    
    kb.button(text=_("🔙 Назад"), callback_data="admin_items")
    kb.adjust(2, 2, 2, 1, 1)

    try:
        if is_new_message:
            if item.get('photo_path'):
                await callback.message.answer_photo(
                    photo=FSInputFile(item['photo_path']),
                    caption=text,
                    reply_markup=kb.as_markup()
                )
            else:
                await callback.message.answer(
                    text=text,
                    reply_markup=kb.as_markup()
                )
        else:
            if item.get('photo_path'):
                try:
                    await callback.message.delete()
                except:
                    pass
                await callback.message.answer_photo(
                    photo=FSInputFile(item['photo_path']),
                    caption=text,
                    reply_markup=kb.as_markup()
                )
            else:
                await callback.message.edit_text(
                    text=text,
                    reply_markup=kb.as_markup()
                )
    except Exception as e:
        logger.error(f"Ошибка при отображении меню: {e}")
        await callback.message.answer(
            text=text,
            reply_markup=kb.as_markup()
        )


@admin.callback_query(F.data == "change_name")
async def change_name_start(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(EditItemStates.waiting_for_new_name)
        await callback.message.answer(
            _("✏️ Введите новое название товара:"),
            reply_markup=InlineKeyboardBuilder()
                .button(text=_("🔙 Отмена"), callback_data="cancel_edit")
                .as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка при запросе нового названия: {e}")
        await callback.answer("Не удалось начать изменение", show_alert=True)

@admin.message(EditItemStates.waiting_for_new_name)
async def process_new_name(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        item_id = data['item_id']

        await db.items.update_item(item_id, name=message.text)
        item = await db.items.get_item(item_id)
        await state.update_data(current_item=item)

        await message.answer(_("✅ Название товара успешно обновлено!"))

        # 🔧 Вместо создания CallbackQuery вручную вызываем show_item_edit_menu напрямую
        from aiogram.types import CallbackQuery
        class DummyCallback:
            def __init__(self, message):
                self.message = message

        await show_item_edit_menu(
            DummyCallback(message),  # эмуляция callback.message
            item,
            is_new_message=True
        )

    except Exception as e:
        logger.error(f"Ошибка при обновлении названия: {e}")
        await message.answer("Произошла ошибка при обновлении")

# Обработчики изменения описания
@admin.callback_query(F.data == "change_description")
async def change_description_start(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(EditItemStates.waiting_for_new_description)
        await callback.message.answer(
            _("📝 Введите новое описание товара:"),
            reply_markup=InlineKeyboardBuilder()
                .button(text=_("🔙 Отмена"), callback_data="cancel_edit")
                .as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка при запросе нового описания: {e}")
        await callback.answer("Не удалось начать изменение", show_alert=True)


@admin.message(EditItemStates.waiting_for_new_description)
async def process_new_description(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        item_id = data['item_id']

        await db.items.update_item(item_id, description=message.text)
        item = await db.items.get_item(item_id)
        await state.update_data(current_item=item)

        await message.answer(_("✅ Описание товара успешно обновлено!"))

        from aiogram.types import CallbackQuery
        class DummyCallback:
            def __init__(self, message):
                self.message = message

        await show_item_edit_menu(
            DummyCallback(message),
            item,
            is_new_message=True
        )

    except Exception as e:
        logger.error(f"Ошибка при обновлении описания: {e}")
        await message.answer("Произошла ошибка при обновлении")
        
# Обработчики изменения цены
@admin.callback_query(F.data == "change_price")
async def change_price_start(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(EditItemStates.waiting_for_new_price)
        await callback.message.answer(
            _("💰 Введите новую цену товара (только число):"),
            reply_markup=InlineKeyboardBuilder()
                .button(text=_("🔙 Отмена"), callback_data="cancel_edit")
                .as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка при запросе новой цены: {e}")
        await callback.answer("Не удалось начать изменение", show_alert=True)

@admin.message(EditItemStates.waiting_for_new_price)
async def process_new_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        if price <= 0:
            raise ValueError

        data = await state.get_data()
        item_id = data['item_id']

        await db.items.update_item(item_id, price=price)
        item = await db.items.get_item(item_id)
        await state.update_data(current_item=item)

        await message.answer(_("✅ Цена товара успешно обновлена!"))

        class DummyCallback:
            def __init__(self, message):
                self.message = message

        await show_item_edit_menu(DummyCallback(message), item, is_new_message=True)

    except ValueError:
        await message.answer(_("❌ Неверный формат цены! Введите положительное число:"))
    except Exception as e:
        logger.error(f"Ошибка при обновлении цены: {e}")
        await message.answer("Произошла ошибка при обновлении")


# Обработчики изменения инструкции
@admin.callback_query(F.data == "change_instruction")
async def change_instruction_start(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(EditItemStates.waiting_for_new_instruction)
        await callback.message.answer(
            _("📄 Введите новую инструкцию для товара (или отправьте '-' чтобы удалить):"),
            reply_markup=InlineKeyboardBuilder()
                .button(text=_("🔙 Отмена"), callback_data="cancel_edit")
                .as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка при запросе новой инструкции: {e}")
        await callback.answer("Не удалось начать изменение", show_alert=True)

@admin.message(EditItemStates.waiting_for_new_instruction)
async def process_new_instruction(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        item_id = data['item_id']
        instruction = message.text if message.text != '-' else None

        await db.items.update_item(item_id, instruction=instruction)
        item = await db.items.get_item(item_id)
        await state.update_data(current_item=item)

        await message.answer(_("✅ Инструкция товара успешно обновлена!"))

        class DummyCallback:
            def __init__(self, message):
                self.message = message

        await show_item_edit_menu(DummyCallback(message), item, is_new_message=True)

    except Exception as e:
        logger.error(f"Ошибка при обновлении инструкции: {e}")
        await message.answer("Произошла ошибка при обновлении")


# Обработчики изменения файла
@admin.callback_query(F.data == "change_file")
async def change_file_start(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(EditItemStates.waiting_for_new_file)
        await callback.message.answer(
            _("📁 Отправьте новый файл плагина (архив или исполняемый файл):"),
            reply_markup=InlineKeyboardBuilder()
                .button(text=_("🔙 Отмена"), callback_data="cancel_edit")
                .as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка при запросе нового файла: {e}")
        await callback.answer("Не удалось начать изменение файла", show_alert=True)


@admin.message(EditItemStates.waiting_for_new_file, F.document)
async def process_new_file(message: Message, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        item_id = data['item_id']
        old_item = data['current_item']

        if old_item.get('file_path') and os.path.exists(old_item['file_path']):
            os.remove(old_item['file_path'])

        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_ext = file.file_path.split('.')[-1]
        file_path = f"plugins/plugin_{uuid.uuid4()}.{file_ext}"

        os.makedirs("plugins", exist_ok=True)
        await bot.download_file(file.file_path, file_path)

        await db.items.update_item(item_id, file_path=file_path)
        item = await db.items.get_item(item_id)
        await state.update_data(current_item=item)

        await message.answer(_("✅ Файл товара успешно обновлен!"))

        class DummyCallback:
            def __init__(self, message):
                self.message = message

        await show_item_edit_menu(DummyCallback(message), item, is_new_message=True)
    except Exception as e:
        logger.error(f"Ошибка при обновлении файла: {e}")
        await message.answer("Произошла ошибка при обновлении файла")


# Обработчики изменения фото
@admin.callback_query(F.data == "change_photo")
async def change_photo_start(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.set_state(EditItemStates.waiting_for_new_photo)
        await callback.message.answer(
            _("🖼 Отправьте новое фото для товара (или отправьте '-' чтобы удалить):"),
            reply_markup=InlineKeyboardBuilder()
                .button(text=_("🔙 Отмена"), callback_data="cancel_edit")
                .as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка при запросе фото: {e}")
        await callback.answer("Не удалось начать изменение фото", show_alert=True)


@admin.message(EditItemStates.waiting_for_new_photo, F.photo)
async def process_new_photo(message: Message, state: FSMContext, bot: Bot):
    try:
        data = await state.get_data()
        item_id = data['item_id']
        old_item = data['current_item']

        if old_item.get('photo_path') and os.path.exists(old_item['photo_path']):
            os.remove(old_item['photo_path'])

        photo_id = message.photo[-1].file_id
        photo = await bot.get_file(photo_id)
        photo_ext = photo.file_path.split('.')[-1]
        photo_path = f"photos/photo_{uuid.uuid4()}.{photo_ext}"

        os.makedirs("photos", exist_ok=True)
        await bot.download_file(photo.file_path, photo_path)

        await db.items.update_item(item_id, photo_path=photo_path)
        item = await db.items.get_item(item_id)
        await state.update_data(current_item=item)

        await message.answer(_("✅ Фото товара успешно обновлено!"))

        class DummyCallback:
            def __init__(self, message):
                self.message = message

        await show_item_edit_menu(DummyCallback(message), item, is_new_message=True)
    except Exception as e:
        logger.error(f"Ошибка при обновлении фото: {e}")
        await message.answer("Произошла ошибка при обновлении фото")

# Выгрузка файла
@admin.callback_query(F.data == "download_file")
async def download_file_handler(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    item = data['current_item']
    
    if not item.get('file_path') or not os.path.exists(item['file_path']):
        await callback.answer(_("Файл не найден!"), show_alert=True)
        return
    
    try:
        await bot.send_document(
            chat_id=callback.from_user.id,
            document=FSInputFile(item['file_path']),
            caption=_("📦 Файл плагина: {}").format(item['name'])
        )
        await callback.answer(_("Файл отправлен вам в личные сообщения"), show_alert=True)
    except Exception as e:
        print(f"Ошибка при отправке файла: {e}")
        await callback.answer(_("Не удалось отправить файл!"), show_alert=True)

# Активация/деактивация товара
@admin.callback_query(F.data == "toggle_active")
async def toggle_active_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item_id = data['item_id']
    item = data['current_item']
    
    new_status = not item.get('is_active', True)
    await db.items.update_item(item_id, is_active=new_status)
    
    # Обновляем данные в состоянии
    item['is_active'] = new_status
    await state.update_data(current_item=item)
    
    await callback.answer(
        _("Товар {}активирован").format("" if new_status else "де"),
        show_alert=False
    )
    
    # Показываем обновленное меню
    await show_item_edit_menu(callback, item)

@admin.callback_query(F.data == "cancel_edit")
async def cancel_edit_handler(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    item_id = data['item_id']
    item = data['current_item']
    await state.set_state(EditItemStates.waiting_for_item_select)
    await show_item_edit_menu(callback, item)