from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold, hlink, hcode, hitalic

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


from aiogram.utils.i18n import I18n, gettext as _, SimpleI18nMiddleware
from aiogram.utils.i18n.middleware import FSMI18nMiddleware
import logging

logger = logging.getLogger(__name__)

# Инициализация i18n
i18n = I18n(path="locales", default_locale="ru", domain="messages")

# Создаем middleware
i18n_middleware = SimpleI18nMiddleware(i18n=i18n)

def setup_i18n(dispatcher):
    # Устанавливаем middleware для всех типов апдейтов
    dispatcher.message.outer_middleware.register(i18n_middleware)
    dispatcher.callback_query.outer_middleware.register(i18n_middleware)
    dispatcher.inline_query.outer_middleware.register(i18n_middleware)
    dispatcher.chat_member.outer_middleware.register(i18n_middleware)
    dispatcher.my_chat_member.outer_middleware.register(i18n_middleware)

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

class UserLanguageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if user:
            from .db_init import db
            user_data = await db.users.get_user(user.id)
            if user_data and user_data.get("language"):
                data["locale"] = user_data["language"]
                data["_"] = i18n.gettext
            else:
                # fallback: установить язык из Telegram
                lang_code = getattr(user, "language_code", "ru")
                data["locale"] = lang_code
                i18n.ctx_locale.set(lang_code)
                data["_"] = i18n.gettext
        return await handler(event, data)


class MyI18nMiddleware(SimpleI18nMiddleware):
    async def get_locale(self, event, data):
        user_id = event.from_user.id
        from .db_init import db
        user = await db.users.get_user(user_id)
        return user['language'] if user else 'ru'
