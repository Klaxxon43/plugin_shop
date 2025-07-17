import uuid
from datetime import datetime, timedelta
from database.create import DataBase

class DepositsDB:
    def __init__(self, db: DataBase):
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
            await cur.execute('''
                SELECT * FROM deposits WHERE unique_id = ?
            ''', (unique_id,))
            return await cur.fetchone()

    async def update_deposit_status(self, unique_id: str, status: str):
        async with self.db.con.cursor() as cur:
            await cur.execute('''
                UPDATE deposits SET status = ? WHERE unique_id = ?
            ''', (status, unique_id))
            await self.db.con.commit()