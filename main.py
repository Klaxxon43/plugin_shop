# main.py
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode

from handlers.client.menu import router 
from handlers.admin.admin import admin
from utils.imports import *

async def main():
    # Проверяем и создаем конфиг если нужно
    if not Path("config.cfg").exists():
        create_config()

    # Инициализация бота и диспетчера
    bot = Bot(token=config['bot']['token'], default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Подключение роутеров
    dp.include_router(router)
    dp.include_router(admin)

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())