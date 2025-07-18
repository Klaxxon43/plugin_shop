import aiosqlite
import pytz
from datetime import datetime
import os, uuid
from datetime import timedelta
from utils.imports import Bot, _


MOSCOW_TZ = pytz.timezone("Europe/Moscow")

class DataBase:
    def __init__(self):
        self.con = None  # Будет установлено в create()
        
        # Инициализируем подклассы
        self.users = self.Users(self)
        self.items = self.Items(self)
        self.deposits = self.Deposits(self)
        self.op = self.Op(self)
        self.history = self.History(self)

    async def create(self):
        """Инициализация БД и создание таблиц"""
        os.makedirs('data', exist_ok=True)
        self.con = await aiosqlite.connect('data/users.db')
        print('БД подключена')

        async with self.con.cursor() as cur:
            # Таблица пользователей
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    username TEXT,
                    balance REAL DEFAULT 0,
                    rub_balance REAL DEFAULT 0,
                    referrer_id INTEGER DEFAULT NULL,
                    is_banned BOOLEAN DEFAULT FALSE,
                    reg_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    language TEXT DEFAULT 'ru',
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица товаров
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    price REAL,
                    instruction TEXT,
                    file_path TEXT,
                    photo_path TEXT,
                    purchases_count INTEGER DEFAULT 0
                )
            ''')
            
            # Таблица депозитов
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS deposits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unique_id TEXT UNIQUE,
                    user_id INTEGER,
                    amount REAL,
                    date_start TIMESTAMP,
                    date_end TIMESTAMP,
                    service TEXT,
                    item_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            ''')
            
            # Таблица ОП каналов
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS op_channels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT UNIQUE
                )
            ''')
            
            # Таблица истории операций
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount REAL,
                    comment TEXT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Таблица языков пользователей
            await cur.execute('''
                CREATE TABLE IF NOT EXISTS user_languages (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'ru',
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            await self.con.commit()

    # Вложенные классы для работы с таблицами
    class Users:
        def __init__(self, db):
            self.db = db

        async def add_user(self, user_id, username, referrer_id=None, language="ru"):
            async with self.db.con.cursor() as cur:
                await cur.execute("""
                    INSERT INTO users (user_id, username, referrer_id, language)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, referrer_id, language))
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
                # Получаем данные пользователя (включая язык)
                await cur.execute('''
                    SELECT * FROM users WHERE user_id = ?
                ''', (user_id,))
                user_data = await cur.fetchone()

                if not user_data:
                    return None

                # Преобразуем кортеж в словарь
                columns = [desc[0] for desc in cur.description]
                user = dict(zip(columns, user_data))

                return user
            
        async def get_user_id_by_username(self, username: int):
            async with self.db.con.cursor() as cur:
                # Получаем данные пользователя (включая язык)
                await cur.execute('''
                    SELECT * FROM users WHERE username = ?
                ''', (username,))
                user_data = await cur.fetchone()

                if not user_data:
                    return None

                # Преобразуем кортеж в словарь
                columns = [desc[0] for desc in cur.description]
                user = dict(zip(columns, user_data))

                return user['user_id']


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
            
        async def update_user(self, user_id: int, **kwargs):
            async with self.db.con.cursor() as cur:
                set_clause = ', '.join(f"{k} = ?" for k in kwargs)
                values = list(kwargs.values())
                values.append(user_id)
                
                await cur.execute(f'''
                    UPDATE users SET {set_clause} WHERE user_id = ?
                ''', values)
                await self.db.con.commit()
                
        async def get_ref_count(self, user_id: int) -> int:
            """Получить количество рефералов пользователя"""
            async with self.db.con.cursor() as cur:
                await cur.execute('SELECT COUNT(*) FROM users WHERE referrer_id = ?', (user_id,))
                return (await cur.fetchone())[0]
        
        async def get_ref_income(self, user_id: int) -> float:
            """Получить суммарный доход от рефералов (из истории операций)"""
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM history 
                    WHERE user_id = ? AND comment LIKE 'Реферальный бонус%'
                ''', (user_id,))
                return (await cur.fetchone())[0]
        
        async def add_ref_income(self, user_id: int, amount: float):
            """Добавить доход от реферала через историю операций"""
            async with self.db.con.cursor() as cur:
                # Добавляем запись в историю
                await cur.execute('''
                    INSERT INTO history (user_id, amount, comment, date)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (user_id, amount, f"Реферальный бонус: +{amount}₽"))
                
                # Обновляем баланс пользователя
                await cur.execute('''
                    UPDATE users 
                    SET balance = balance + ? 
                    WHERE user_id = ?
                ''', (amount, user_id))
                await self.db.con.commit()
        
        async def get_referrer(self, user_id: int):
            """Получить реферера пользователя"""
            async with self.db.con.cursor() as cur:
                await cur.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
                result = await cur.fetchone()
                return result[0] if result else None
                
        async def execute_query(self, query):
            """Выполняет SQL-запрос и возвращает результат."""
            try:
                async with self.db.con.cursor() as cur:
                    await cur.execute(query)
                    result = await cur.fetchall()
                    return result
            except Exception as e:
                return f"Ошибка при выполнении запроса: {e}"
                
        async def get_db_structure_sqlite(self):
            """Получение структуры базы данных."""
            try:
                async with self.db.con.cursor() as cur:
                    # Получаем список всех таблиц
                    await cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = await cur.fetchall()

                    db_structure = {}

                    # Для каждой таблицы получаем информацию о колонках
                    for table in tables:
                        table_name = table[0]
                        await cur.execute(f"PRAGMA table_info({table_name});")
                        columns = await cur.fetchall()
                        db_structure[table_name] = columns

                    return db_structure
            except Exception as e:
                print(f"Ошибка: {e}")
                return {}
            
    class Items:
        def __init__(self, db):
            self.db = db

        async def add_item(self, name: str, description: str, price: float, 
                        instruction: str, file_path: str, photo_path: str = None):
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    INSERT INTO items (name, description, price, instruction, file_path, photo_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, description, price, instruction, file_path, photo_path))
                await self.db.con.commit()

        async def get_item(self, item_id: int):
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    SELECT * FROM items WHERE id = ?
                ''', (item_id,))
                
                item_data = await cur.fetchone()
                
                if not item_data:
                    return None
                
                columns = [column[0] for column in cur.description]
                item_dict = dict(zip(columns, item_data))
                
                return item_dict

        async def get_all_items(self, page: int = 1, per_page: int = 5):
            async with self.db.con.cursor() as cur:
                offset = (page - 1) * per_page
                await cur.execute('SELECT * FROM items LIMIT ? OFFSET ?', (per_page, offset))
                
                columns = [column[0] for column in cur.description]
                items = []
                for row in await cur.fetchall():
                    items.append(dict(zip(columns, row)))
                
                return items

        async def update_item(self, item_id: int, **kwargs):
            async with self.db.con.cursor() as cur:
                # Проверяем, есть ли photo_path в kwargs
                if 'photo_path' in kwargs and kwargs['photo_path'] is None:
                    # Если photo_path явно установлен в None, обновляем его в БД как NULL
                    set_clause = ', '.join(f"{k} = ?" for k in kwargs if k != 'photo_path')
                    set_clause += ', photo_path = NULL' if set_clause else 'photo_path = NULL'
                    values = [v for k, v in kwargs.items() if k != 'photo_path']
                else:
                    # Обычное обновление
                    set_clause = ', '.join(f"{k} = ?" for k in kwargs)
                    values = list(kwargs.values())
                
                values.append(item_id)
                
                await cur.execute(f'''
                    UPDATE items SET {set_clause} WHERE id = ?
                ''', values)
                await self.db.con.commit()

        async def delete_item(self, item_id: int):
            async with self.db.con.cursor() as cur:
                # Сначала получаем информацию о товаре для удаления файлов
                item = await self.get_item(item_id)
                if item:
                    # Здесь можно добавить удаление файлов с диска
                    # os.remove(item['file_path'])
                    # if item['photo_path']: os.remove(item['photo_path'])
                    pass
                    
                await cur.execute('DELETE FROM items WHERE id = ?', (item_id,))
                await self.db.con.commit()

        async def increment_purchases(self, item_id: int):
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    UPDATE items SET purchases_count = purchases_count + 1 WHERE id = ?
                ''', (item_id,))
                await self.db.con.commit()

        async def update_item_photo(self, item_id: int, photo_path: str):
            """Специальный метод для обновления только фото"""
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    UPDATE items SET photo_path = ? WHERE id = ?
                ''', (photo_path, item_id))
                await self.db.con.commit()

        async def remove_item_photo(self, item_id: int):
            """Специальный метод для удаления фото"""
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    UPDATE items SET photo_path = NULL WHERE id = ?
                ''', (item_id,))
                await self.db.con.commit()
                
    class Deposits:
        def __init__(self, db):
            self.db = db

        async def create_deposit(self, user_id: int, amount: float, service: str, item_id: int = None):
            unique_id = str(uuid.uuid4())
            date_start = datetime.now()
            date_end = date_start + timedelta(hours=1)
            
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    INSERT INTO deposits (unique_id, user_id, amount, date_start, date_end, service, item_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (unique_id, user_id, amount, date_start, date_end, service, item_id))
                await self.db.con.commit()
            
            return unique_id

        async def get_deposit(self, unique_id: str):
            async with self.db.con.cursor() as cur:
                await cur.execute('SELECT * FROM deposits WHERE unique_id = ?', (unique_id,))
                return await cur.fetchone()

        async def update_deposit_status(self, unique_id: str, status: str):
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    UPDATE deposits SET status = ? WHERE unique_id = ?
                ''', (status, unique_id))
                await self.db.con.commit()

    class Op:
        def __init__(self, db):  # Принимает db (экземпляр DataBase)
            self.db = db

        async def get_op_channels(self):
            async with self.db.con.cursor() as cur:
                await cur.execute('SELECT * FROM op_channels')
                columns = [column[0] for column in cur.description]
                return [dict(zip(columns, row)) for row in await cur.fetchall()]

        async def add_op_channel(self, channel_id: str):
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    INSERT OR IGNORE INTO op_channels (channel_id) VALUES (?)
                ''', (channel_id,))
                await self.db.con.commit()

        async def remove_op_channel(self, channel_id: str):
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    DELETE FROM op_channels WHERE channel_id = ?
                ''', (channel_id,))
                await self.db.con.commit()

        async def update_channel_url(self, channel_id: int, new_url: str):
            async with self.db.con.cursor() as cur:
                await cur.execute(
                    "UPDATE op_channels SET channel_id = ? WHERE id = ?",
                    (new_url, channel_id)
                )
                await self.db.con.commit()


    class History:
        def __init__(self, db):
            self.db = db

        async def add_record(self, user_id: int, amount: float, comment: str):
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    INSERT INTO history (user_id, amount, comment, date)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (user_id, amount, comment))
                await self.db.con.commit()

        async def get_user_history(self, user_id: int, limit: int = 10):
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    SELECT * FROM history 
                    WHERE user_id = ? 
                    ORDER BY date DESC 
                    LIMIT ?
                ''', (user_id, limit))
                return await cur.fetchall()

        async def get_all_history(self, limit: int = 100):
            async with self.db.con.cursor() as cur:
                await cur.execute('''
                    SELECT * FROM history 
                    ORDER BY date DESC 
                    LIMIT ?
                ''', (limit,))
                return await cur.fetchall()

        async def get_stats(self):
            async with self.db.con.cursor() as cur:
                # Общее количество операций
                await cur.execute('SELECT COUNT(*) FROM history')
                total = (await cur.fetchone())[0]
                
                # Сумма всех пополнений
                await cur.execute('SELECT SUM(amount) FROM history WHERE amount > 0')
                income = (await cur.fetchone())[0] or 0
                
                # Сумма всех выводов
                await cur.execute('SELECT SUM(amount) FROM history WHERE amount < 0')
                outcome = (await cur.fetchone())[0] or 0
                
                return {
                    'total': total,
                    'income': income,
                    'outcome': outcome,
                    'balance': income + outcome
                } 