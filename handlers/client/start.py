from aiogram import Bot, types, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

import configparser
from database.create import DataBase
from utils.db_init import db
from utils.imports import _
from utils.imports import *

from .menu import router

@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    lang_code = message.from_user.language_code or "ru"  # Telegram может вернуть None

    # Обработка реферальной ссылки
    ref_id = None
    if len(message.text.split()) > 1:
        ref_id = message.text.split()[1]
        
        # Проверяем, что реферер существует и это не сам пользователь
        if str(ref_id) == str(user_id):
            ref_id = None
        else:
            ref_user = await db.users.get_user(int(ref_id))
            if not ref_user:
                ref_id = None

    # Регистрация пользователя
    if not await db.users.get_user(user_id):
        await db.users.add_user(user_id, username, ref_id, language=lang_code)
        
        # Отправляем уведомление рефереру
        if ref_id:
            try:
                await message.bot.send_message(
                    ref_id,
                    _("🎉 У вас новый реферал! Пользователь @{username} присоединился по вашей ссылке.").format(
                        username=username if username else "без username"
                    )
                )
            except:
                pass  # Если не удалось отправить сообщение
    
    # Проверка подписок на каналы (раскомментируйте если нужно)
    if not await db.users.check_subs(user_id, message.bot):
        await show_op_channels(message, message.bot)
        return
    
    # Показываем главное меню
    await show_main_menu(message, user_id)

async def show_op_channels(message: Message, bot: Bot):
    op_channels = await db.op.get_op_channels()
    valid_channels = []
    kb = InlineKeyboardBuilder()
    
    for channel in op_channels:
        try:
            channel_id = channel['channel_id']
            print(f"Проверка канала: {channel_id}")
            
            # Получаем информацию о канале
            chat = await bot.get_chat(channel_id)
            
            # Проверяем, что бот является администратором
            bot_member = await bot.get_chat_member(chat.id, bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                print(f"Бот не админ в канале {channel_id}")
                continue
                
            # Проверяем необходимые права (минимум - просмотр участников)
            if not bot_member.can_restrict_members and not bot_member.can_promote_members:
                print(f"У бота недостаточно прав в канале {channel_id}")
                continue
                
            # Формируем ссылку в зависимости от типа канала
            if chat.username:
                url = f"https://t.me/{chat.username}"
            else:
                try:
                    invite = await chat.export_invite_link()
                    url = invite
                except:
                    print(f"Не удалось получить ссылку для канала {channel_id}")
                    continue
            
            # Добавляем валидный канал
            valid_channels.append(chat)
            kb.add(InlineKeyboardButton(
                text=_("Подписаться на {channel}").format(channel=chat.title),
                url=url
            ))
            
        except Exception as e:
            print(f"Ошибка при проверке канала {channel.get('channel_id', 'unknown')}: {str(e)}")
            continue
    
    if not valid_channels:
        await message.answer(_("❌ Нет доступных каналов для подписки. Обратитесь к администратору."))
        return
    
    # Добавляем кнопку проверки подписки
    kb.add(InlineKeyboardButton(
        text=_("✅ Я подписался"),
        callback_data="back_menu"
    ))
    kb.adjust(1)
    
    await message.answer(
        _("📢 <b>Для использования бота необходимо подписаться на наши каналы:</b>"),
        reply_markup=kb.as_markup()
    )

async def show_main_menu(message: types.Message, user_id: int):
    is_admin = user_id in admins_list
    
    text = _("<b>Главное меню</b>")
    
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text=_("🧩 Плагины"), callback_data="plugins"))
    kb.add(InlineKeyboardButton(text=_("🎩 Профиль"), callback_data="profile"))
    kb.add(InlineKeyboardButton(text=_("👥 Реф система"), callback_data="ref_system"))
    kb.add(InlineKeyboardButton(text=_("ℹ️ О нас"), callback_data="about"))
    
    if is_admin:
        kb.add(InlineKeyboardButton(text=_("🛠 АДМИНКА"), callback_data="admin_panel"))

    kb.adjust(2, 1, 1, 1)

    await message.answer(text, reply_markup=kb.as_markup())