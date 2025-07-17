from datetime import datetime
from utils.imports import _
from .create import DataBase

class HistoryDB:
    def __init__(self, db: DataBase):
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