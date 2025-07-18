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
    await show_plugins_page(callback, page=1)


@router.callback_query(F.data.startswith("plugins_page_"))
async def plugins_page_handler(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[-1])
    await show_plugins_page(callback, page=page)


async def show_plugins_page(callback: types.CallbackQuery, page: int = 1):
    all_items = await db.items.get_all_items()
    per_page = config.items_per_page
    total_items = len(all_items)
    total_pages = (total_items + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    items = all_items[start:end]

    if not items:
        await callback.message.edit_text(
            _("🧩 На данный момент нет доступных плагинов."),
            reply_markup=back_kb()
        )
        return

    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(
            text=f"{item['name']} - {item['price']}₽",
            callback_data=f"plugin_{item['id']}"
        )
    builder.adjust(1)

    if total_pages > 0:
        prev_page = page - 1 if page > 1 else total_pages
        next_page = page + 1 if page < total_pages else 1
        builder.row(
            InlineKeyboardButton(text="◀️", callback_data=f"plugins_page_{prev_page}"),
            InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="noop"),
            InlineKeyboardButton(text="▶️", callback_data=f"plugins_page_{next_page}")
        )

    builder.row(InlineKeyboardButton(text=_("🔙 Назад"), callback_data="back_menu"))

    await callback.message.delete()
    await callback.message.answer(
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

    text = _('''🧩 <b>{name}</b>

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

    if item.get('photo_path'):
        try:
            with open(item['photo_path'], 'rb') as photo:
                media = types.InputMediaPhoto(
                    media=types.BufferedInputFile(photo.read(), filename="item_photo.jpg"),
                    caption=text,
                    parse_mode="HTML"
                )
                await callback.message.edit_media(
                    media=media,
                    reply_markup=kb.as_markup()
                )
        except Exception as e:
            print(f"Ошибка при отправке фото: {e}")
            await callback.message.edit_text(text, reply_markup=kb.as_markup())
    else:
        await callback.message.edit_text(text, reply_markup=kb.as_markup())


def back_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text=_("🔙 Назад"), callback_data="back_menu")
    kb.adjust(1)
    return kb.as_markup()


@router.message(Command("GetAIIPlugins"))
async def all_plugins_command(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    if user_id in admins_list:
        return
    
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