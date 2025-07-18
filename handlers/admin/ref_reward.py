from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from configparser import ConfigParser
from utils.imports import _
from utils.imports import *

from .admin import admin

class RefPercentStates(StatesGroup):
    waiting_for_new_percent = State()

class CryptoBotStates(StatesGroup):
    waiting_for_new_token = State()

class AdminStates(StatesGroup):
    waiting_for_new_admins = State()

@admin.message(Command("set_cryptobot_token"))
async def set_cryptobot_token_handler(message: Message, state: FSMContext):
    if message.from_user.id not in map(int, config.get("bot", "admins").split(",")):
        return await message.answer(_("❌ У вас нет прав на эту команду!"))
    
    await state.set_state(CryptoBotStates.waiting_for_new_token)
    await message.answer(
        _("🔑 Текущий токен CryptoBot: {current}\n"
          "Введите новый токен:").format(
              current=config.get("bot", "cryptobot_token")
          ),
        reply_markup=types.ReplyKeyboardRemove()
    )

@admin.message(CryptoBotStates.waiting_for_new_token, F.text)
async def process_new_token(message: Message, state: FSMContext):
    new_token = message.text.strip()
    
    # Простая валидация токена (можно добавить более сложную проверку)
    if len(new_token) < 20:  # Минимальная длина токена
        await message.answer(_("❌ Токен слишком короткий! Введите корректный токен:"))
        return
    
    # Обновляем конфиг
    config.set("bot", "cryptobot_token", new_token)
    
    # Сохраняем в файл
    with open("config.cfg", "w") as configfile:
        config.write(configfile)
    
    await message.answer(
        _("✅ Токен CryptoBot успешно обновлен!\n"
          "Изменения вступят в силу после перезагрузки бота")
    )
    await state.clear()


@admin.message(Command("set_admins"))
async def set_admins_handler(message: Message, state: FSMContext):
    if message.from_user.id not in map(int, config.get("bot", "admins").split(",")):
        return await message.answer(_("❌ У вас нет прав на эту команду!"))
    
    current_admins = config.get("bot", "admins")
    await state.set_state(AdminStates.waiting_for_new_admins)
    await message.answer(
        _("👥 Текущий список администраторов (ID через запятую):\n"
          "<code>{current}</code>\n\n"
          "Введите новый список администраторов (ID через запятую):").format(
              current=current_admins
          ),
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode="HTML"
    )

@admin.message(AdminStates.waiting_for_new_admins, F.text)
async def process_new_admins(message: Message, state: FSMContext):
    try:
        new_admins = message.text.strip()
        
        # Валидация ввода
        admins_list = [admin_id.strip() for admin_id in new_admins.split(",")]
        for admin_id in admins_list:
            if not admin_id.isdigit():
                raise ValueError
        
        # Обновляем конфиг
        config.set("bot", "admins", new_admins)
        
        # Сохраняем в файл
        with open("config.cfg", "w") as configfile:
            config.write(configfile)
        
        # Обновляем глобальную переменную
        admins_list = list(map(int, admins_list))
        
        await message.answer(
            _("✅ Список администраторов успешно обновлен!\n"
              "Новый список: <code>{new_admins}</code>").format(
                  new_admins=new_admins
              ),
            parse_mode="HTML"
        )
        await state.clear()
        
    except ValueError:
        await message.answer(_("❌ Неверный формат! Введите ID через запятую (только цифры):"))

@admin.message(Command("set_ref_percent"))
async def set_ref_percent_handler(message: Message, state: FSMContext):
    if message.from_user.id not in map(int, config.get("bot", "admins").split(",")):
        return await message.answer(_("❌ У вас нет прав на эту команду!"))
    
    await state.set_state(RefPercentStates.waiting_for_new_percent)
    await message.answer(
        _("📊 Текущий реферальный процент: {current}%\n"
          "Введите новое значение (0-100):").format(
              current=config.getint("bot", "ref_percent")
          ),
        reply_markup=types.ReplyKeyboardRemove()
    )

@admin.message(RefPercentStates.waiting_for_new_percent, F.text)
async def process_new_percent(message: Message, state: FSMContext):
    try:
        new_percent = int(message.text)
        if not 0 <= new_percent <= 100:
            raise ValueError
        
        # Обновляем конфиг
        config.set("bot", "ref_percent", str(new_percent))
        
        # Сохраняем в файл
        with open("config.cfg", "w") as configfile:
            config.write(configfile)
        
        await message.answer(
            _("✅ Реферальный процент успешно изменен на {new_percent}%\nИзменения вступят в силу после перезагрузки бота").format(
                new_percent=new_percent
            )
        )
        await state.clear()
        
    except ValueError:
        await message.answer(_("❌ Неверное значение! Введите число от 0 до 100:"))

