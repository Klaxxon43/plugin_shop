# utils/imports.py
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold, hlink, hcode, hitalic

import configparser
import logging
import os
import uuid
import aiosqlite
import pytz, asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union

from configparser import ConfigParser
from pathlib import Path

# Для локализации
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware, FSMI18nMiddleware
from aiogram.utils.i18n.middleware import ConstI18nMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
) 
logger = logging.getLogger(__name__)

i18n = I18n(path="locales", default_locale="ru", domain="messages")
_ = i18n.gettext

def create_config():
    """Создает конфигурационный файл с запросом данных у пользователя"""
    config = ConfigParser()
    
    print("Конфигурационный файл не найден. Давайте создадим его!")
    bot_token = input("Введите токен вашего бота: ")
    cryptobot_token = input("Введите токен CryptoBot: ")
    admin_id = input("Введите ваш ID в Telegram (можно узнать у @userinfobot): ")
    
    config['bot'] = {
        'token': bot_token,
        'admins': admin_id,
        'items_per_page': '5',
        'ref_percent': '15',
        'cryptobot_token': cryptobot_token
    }
    
    with open('config.cfg', 'w') as configfile:
        config.write(configfile)
    
    print("Конфигурационный файл успешно создан!")

# Загружаем конфиг
config = ConfigParser()
if not Path("config.cfg").exists():
    create_config()
config.read("config.cfg")

admins_str = config['bot']['admins']  # строка, например "5129878568,987654321"
admins_list = list(map(int, admins_str.split(',')))  # преобразуем в [5129878568, 987654321]