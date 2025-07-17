from datetime import datetime
from aiogram import Bot
from utils.config_loader import config
from utils.imports import _
from .create import DataBase

class UsersDB:
    def __init__(self, db: DataBase):
        self.db = db

    async def add_user(self, user_id: int, username: str, ref_id: str = None):
        async with self.db.con.cursor() as cur:
            # Проверяем есть ли пользователь
            await cur.execute('SELECT 1 FROM users WHERE user_id = ?', (user_id,))
            if await cur.fetchone():
                return
            
            # Проверяем реферала
            referrer_id = None
            if ref_id and ref_id.isdigit():
                referrer_id = int(ref_id)
                await cur.execute('SELECT 1 FROM users WHERE user_id = ?', (referrer_id,))
                if not await cur.fetchone():
                    referrer_id = None
            
            # Добавляем пользователя
            await cur.execute('''
                INSERT INTO users (user_id, username, referrer_id, reg_time)
                VALUES (?, ?, ?, datetime('now'))
            ''', (user_id, username, referrer_id))
            
            # Добавляем язык по умолчанию
            await cur.execute('''
                INSERT OR IGNORE INTO user_languages (user_id, language)
                VALUES (?, 'ru')
            ''', (user_id,))
            
            # Уведомляем реферала
            if referrer_id:
                try:
                    bot = Bot.get_current()
                    await bot.send_message(
                        referrer_id,
                        _("🎉 Пользователь @{username} перешёл по вашей ссылке и стал вашим рефералом!").format(username=username)
                    )
                except Exception as e:
                    print(f"Не удалось уведомить реферала: {e}")
            
            await self.db.con.commit()

    async def check_subs(self, user_id: int, bot: Bot) -> bool:
        async with self.db.con.cursor() as cur:
            await cur.execute('SELECT channel_id FROM op_channels')
            channels = await cur.fetchall()
            
            for channel in channels:
                try:
                    member = await bot.get_chat_member(channel[0], user_id)
                    if member.status not in ['member', 'administrator', 'creator']:
                        return False
                except Exception as e:
                    print(f"Ошибка проверки подписки: {e}")
                    continue
            
            return True

    async def get_user(self, user_id: int):
        async with self.db.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM users WHERE user_id = ?
            ''', (user_id,))
            user = await cur.fetchone()
            
            if user:
                await cur.execute('''
                    SELECT language FROM user_languages WHERE user_id = ?
                ''', (user_id,))
                lang = await cur.fetchone()
                user['language'] = lang[0] if lang else 'ru'
            
            return user

    async def update_balance(self, user_id: int, amount: float, comment: str):
        async with self.db.con.cursor() as cur:
            await cur.execute('''
                UPDATE users SET balance = balance + ? WHERE user_id = ?
            ''', (amount, user_id))
            
            await self.db.history.add_record(user_id, amount, comment)
            await self.db.con.commit()

    async def ban_user(self, user_id: int):
        async with self.db.con.cursor() as cur:
            await cur.execute('''
                UPDATE users SET is_banned = TRUE WHERE user_id = ?
            ''', (user_id,))
            await self.db.con.commit()

    async def unban_user(self, user_id: int):
        async with self.db.con.cursor() as cur:
            await cur.execute('''
                UPDATE users SET is_banned = FALSE WHERE user_id = ?
            ''', (user_id,))
            await self.db.con.commit()

    async def set_language(self, user_id: int, language: str):
        async with self.db.con.cursor() as cur:
            await cur.execute('''
                INSERT OR REPLACE INTO user_languages (user_id, language)
                VALUES (?, ?)
            ''', (user_id, language))
            await self.db.con.commit()

    async def get_all_users(self):
        async with self.db.con.cursor() as cur:
            await cur.execute('SELECT COUNT(*) FROM users')
            total_users = (await cur.fetchone())[0]
            
            await cur.execute('SELECT COUNT(*) FROM users WHERE referrer_id IS NOT NULL')
            ref_users = (await cur.fetchone())[0]
            
            return total_users, ref_users