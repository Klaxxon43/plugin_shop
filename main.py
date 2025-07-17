import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.markdown import hbold
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.i18n import SimpleI18nMiddleware

from database.create import DataBase
from database.users import UsersDB
from database.op import OpDB
from utils.imports import *
from utils.config_loader import config
from handlers.admin.admin import admin
from handlers.client.menu import router

from utils.imports import *
from utils.db_init import *

import configparser

config = configparser.ConfigParser()
config.read("config.cfg")

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=config['bot']['token'], default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    
    dp.message.outer_middleware.register(SimpleI18nMiddleware(i18n))
    dp.callback_query.outer_middleware.register(SimpleI18nMiddleware(i18n))

    dp.message.outer_middleware.register(MyI18nMiddleware(i18n))
    dp.callback_query.outer_middleware.register(MyI18nMiddleware(i18n))

    # Подключение роутеров
    dp.include_router(router)
    router.include_router(admin)

    # Обработчик команды /start
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        username = message.from_user.username
        lang_code = message.from_user.language_code or "ru"  # Telegram может вернуть None

        ref_id = None
        if len(message.text.split()) > 1:
            ref_id = message.text.split()[1]

        if not await db.users.get_user(user_id):
            await db.users.add_user(user_id, username, ref_id, language=lang_code)
            i18n.ctx_locale.set(lang_code) 
        
        # Проверяем подписки на ОП
        # if not await op_db.check_subs(user_id, bot):
        #     await message.answer("Пожалуйста, подпишитесь на наши каналы для использования бота:")
        #     await show_op_channels(message, bot)
        #     return
        
        # Показываем главное меню
        await show_main_menu(message, user_id)
    
    # Запуск бота
    await dp.start_polling(bot)

async def show_op_channels(message: types.Message, bot: Bot):
    op_channels = await db.Op.get_op_channels()
    kb = InlineKeyboardMarkup()
    
    for channel in op_channels:
        chat = await bot.get_chat(channel['channel_id'])
        kb.add(InlineKeyboardButton(
            text=f"Подписаться на {chat.title}",
            url=f"https://t.me/{chat.username}"
        ))
    
    kb.add(InlineKeyboardButton(
        text="Я подписался",
        callback_data="check_subs"
    ))
    
    await message.answer("Подпишитесь на все каналы:", reply_markup=kb)

async def show_main_menu(message: types.Message, user_id: int):
    from utils.imports import _
    admins_str = config['bot']['admins']  # строка, например "5129878568,987654321"
    admins_list = list(map(int, admins_str.split(',')))  # преобразуем в [5129878568, 987654321]

    is_admin = user_id in admins_list
    
    text = _("<b>Главное меню</b>")
    
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=_("🧩 Плагины"), callback_data="plugins"))
    kb.add(InlineKeyboardButton(text=_("👥 Реф система"), callback_data="ref_system"))
    kb.add(InlineKeyboardButton(text=_("ℹ️ О нас"), callback_data="about"))
    
    if is_admin:
        kb.add(InlineKeyboardButton(text=_("🛠 АДМИНКА"), callback_data="admin_panel"))
    kb.adjust(1)

    await message.answer(text, reply_markup=kb.as_markup())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 