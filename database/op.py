from database.create import DataBase

class OpDB:
    def __init__(self, db: DataBase):
        self.db = db

    async def get_op_channels(self):
        async with self.db.con.cursor() as cur:
            await cur.execute('SELECT * FROM op_channels')
            return await cur.fetchall()

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