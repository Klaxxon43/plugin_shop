from database.create import DataBase

class ItemsDB:
    def __init__(self, db: DataBase):
        self.db = db

    async def add_item(self, name: str, description: str, price: float, instruction: str, file_path: str):
        async with self.db.con.cursor() as cur:
            await cur.execute('''
                INSERT INTO items (name, description, price, instruction, file_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, description, price, instruction, file_path))
            await self.db.con.commit()

    async def get_item(self, item_id: int):
        async with self.db.con.cursor() as cur:
            await cur.execute('''
                SELECT * FROM items WHERE id = ?
            ''', (item_id,))
            return await cur.fetchone()

    async def get_all_items(self, page: int = 1, per_page: int = 5):
        async with self.db.con.cursor() as cur:
            offset = (page - 1) * per_page
            await cur.execute('''
                SELECT * FROM items LIMIT ? OFFSET ?
            ''', (per_page, offset))
            return await cur.fetchall()

    async def update_item(self, item_id: int, **kwargs):
        async with self.db.con.cursor() as cur:
            set_clause = ', '.join(f"{k} = ?" for k in kwargs)
            values = list(kwargs.values())
            values.append(item_id)
            
            await cur.execute(f'''
                UPDATE items SET {set_clause} WHERE id = ?
            ''', values)
            await self.db.con.commit()

    async def delete_item(self, item_id: int):
        async with self.db.con.cursor() as cur:
            await cur.execute('''
                DELETE FROM items WHERE id = ?
            ''', (item_id,))
            await self.db.con.commit()

    async def increment_purchases(self, item_id: int):
        async with self.db.con.cursor() as cur:
            await cur.execute('''
                UPDATE items SET purchases_count = purchases_count + 1 WHERE id = ?
            ''', (item_id,))
            await self.db.con.commit()