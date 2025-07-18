from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.imports import _
from utils.imports import *
from utils.db_init import *
from utils.config_loader import config
import aiohttp

from API.CryptoBotAPI import *

from .menu import router 

@router.message(Command('id'))
async def _(message: types.Message, bot: Bot):
    try: 
        username = message.text.split()[1]
        print(username)
        if '@' in username:
            username = username.replace('@', '')
        id = str(await db.users.get_user_id_by_username(username))
        if id:
            await message.answer(f'ID Этого пользователя: <code>{id}</code>')
            return 
        await message.answer(f'У пользователя нет ID')
    except:
        await message.answer(f'Ваш ID: {message.from_user.id}')


@router.message(Command('dbinfo'))
async def handle_db_command(message: types.Message):
    structure = await db.users.get_db_structure_sqlite()

    # Отправляем информацию о таблицах и колонках
    for table, columns in structure.items():
        column_info = []
        for column in columns:
            column_info.append(f"{column[1]} ({column[2]})")  # column[1] - имя колонки, column[2] - тип данных
        await message.answer(f"Таблица: {table}\nКолонки: {', '.join(column_info)}")


@router.message(Command('db'))
async def handle_db_command(message: types.Message):
    user_id = message.from_user.id
    is_admin = user_id in admins_list

    # Проверяем, является ли пользователь администратором
    if not is_admin:
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    # Получаем текст запроса
    if len(message.text.split()) > 1:
        query = ' '.join(message.text.split()[1:])
    print(query)

    if not query:
        await message.answer("❌ Укажите SQL-запрос после команды /db.")
        return
    try: 
        # Выполняем запрос к базе данных
        result = await db.users.execute_query(query)

        # Отправляем результат пользователю
        if isinstance(result, str):  # Если произошла ошибка
            await message.answer(result)
        else:
            # Форматируем результат для удобного отображения
            formatted_result = "\n".join([str(row) for row in result])
            await message.answer(f"✅ Результат запроса:\n<code>{formatted_result}</code>")
    except Exception as e:
        await message.answer(f"❌ Ошибка выполнения запроса: {e}")
        
@router.message(Command('report'))
async def send_report(message: types.Message, bot: Bot):
    # Проверяем, что текст после команды /report не пустой
    if len(message.text.split()) > 1:
        report_text = ' '.join(message.text.split()[1:])  # Получаем текст после команды /report
        
        # Формируем сообщение для админов
        admin_message = (f"""
      🚨 <b>Новый репорт!</b> 🚨
👤 <b>Пользователь:</b> @{message.from_user.username}
🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n
📝 <b>Текст репорта:</b>
<blockquote>{report_text}</blockquote>"""
        )
        # Отправляем сообщение всем админам
        for admin_id in admins_list:
            try:
                await bot.send_message(admin_id, admin_message)
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение админу {admin_id}: {e}")
        
        # Отправляем подтверждение пользователю
        await message.reply("✅ Ваш репорт успешно отправлен админам!")
    else:
        await message.reply("⚠️ Пожалуйста, укажите текст репорта после команды /report.")
