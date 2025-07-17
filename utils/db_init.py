from database import *
from database.create import DataBase
import asyncio 

db = DataBase()
asyncio.run(db.create())  