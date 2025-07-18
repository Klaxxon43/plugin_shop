from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.imports import _
from utils.imports import *
from utils.db_init import *
from utils.config_loader import config
from .menu import router 

@router.callback_query(F.data == "plugins")
async def plugins_handler(callback: types.CallbackQuery, state: FSMContext):
    items = await db.items.get_all_items(page=1, per_page=config.items_per_page)
    
    if not items:
        await callback.message.edit_text(
            _("🧩 На данный момент нет доступных плагинов."),
            reply_markup=back_kb()
        )
        return
    
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.add(InlineKeyboardButton(
            text=f"{item['name']} - {item['price']}₽",
            callback_data=f"plugin_{item['id']}"
        ))
    
    builder.adjust(1)
    
    # Добавляем пагинацию если нужно
    total_items = len(await db.items.get_all_items())
    if total_items > config.items_per_page:
        builder.row(
            InlineKeyboardButton(text="◀️", callback_data="plugins_page_1"),
            InlineKeyboardButton(text="1/1", callback_data="current_page"),
            InlineKeyboardButton(text="▶️", callback_data="plugins_page_2")
        )
    
    builder.row(InlineKeyboardButton(text=_("🔙 Назад"), callback_data="back_menu"))
    
    await callback.message.edit_text(
        _("🧩 <b>Доступные плагины:</b>\n\nВыберите плагин для покупки:"),
        reply_markup=builder.as_markup()
    )

@router.callback_query(F.data.startswith("plugin_"))
async def plugin_detail_handler(callback: types.CallbackQuery, bot: Bot):
    item_id = int(callback.data.split("_")[1])
    item = await db.items.get_item(item_id)
    
    if not item:
        await callback.answer(_("Плагин не найден!"), show_alert=True)
        return
    
    text = _('''
🧩 <b>{name}</b>

💵 <b>Цена:</b> {price}₽
📝 <b>Описание:</b>
{description}

🛒 <b>Купить этот плагин?</b>
''').format(
        name=item['name'],
        price=item['price'],
        description=item['description']
    )
    
    kb = InlineKeyboardBuilder()
    kb.button(text=_("🛒 Купить"), callback_data=f"buy_{item_id}")
    kb.button(text=_("🔙 Назад"), callback_data="plugins")
    kb.adjust(1)
    
    # Если есть фото товара
    if item.get('photo_path'):
        try:
            # Отправляем фото с описанием
            with open(item['photo_path'], 'rb') as photo:
                await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=types.BufferedInputFile(photo.read(), filename='item_photo.jpg'),
                    caption=text,
                    reply_markup=kb.as_markup()
                )
            # Удаляем предыдущее сообщение
            await callback.message.delete()
        except Exception as e:
            print(f"Ошибка при отправке фото: {e}")
            # Если не удалось отправить фото, отправляем просто текст
            await callback.message.edit_text(text, reply_markup=kb.as_markup())
    else:
        # Если фото нет, отправляем просто текст
        await callback.message.edit_text(text, reply_markup=kb.as_markup())

def back_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text=_("🔙 Назад"), callback_data="back_menu")
    kb.adjust(1)
    return kb.as_markup()

@router.message(Command("kerfwekfnrewjkprjefjmkwdernjfeklwfnmekjlwrwenkrdfmewklfewjnrmkewjwl"))
async def all_plugins_command(message: types.Message, bot: Bot):
    # Получаем все плагины из базы данных
    all_items = await db.items.get_all_items()
    
    if not all_items:
        await message.answer(_("🧩 На данный момент нет доступных плагинов."))
        return
    
    # Сначала отправляем текстовую информацию
    response_text = _("🧩 <b>Все доступные плагины и инструкции:</b>\n\n")
    
    for item in all_items:
        response_text += _('''
📌 <b>{name}</b> - {price}₽
📝 <b>Описание:</b> {description}
📖 <b>Инструкция:</b> {instructions}

''').format(
            name=item['name'],
            price=item['price'],
            description=item.get('description', _("Нет описания")),
            instructions=item.get('instruction', _("Инструкция отсутствует"))
        )
    
    # Отправляем текстовую часть
    if len(response_text) > 4096:
        for x in range(0, len(response_text), 4096):
            part = response_text[x:x+4096]
            await message.answer(part)
    else:
        await message.answer(response_text)
    
    # Теперь отправляем файлы для каждого плагина, если они есть
    for item in all_items:
        try:
            # Если есть файл плагина
            if item.get('file_path'):
                with open(item['file_path'], 'rb') as file:
                    await bot.send_document(
                        chat_id=message.chat.id,
                        document=types.BufferedInputFile(
                            file.read(),
                            filename=f"{item['name']}"  # или другое расширение
                        ),
                        caption=_("📦 Файл плагина: {name}").format(name=item['name'])
                    )
            
        except Exception as e:
            print(f"Ошибка при отправке файла для плагина {item['name']}: {e}")
            await message.answer(
                _("⚠️ Не удалось отправить файлы для плагина {name}").format(name=item['name'])
            )