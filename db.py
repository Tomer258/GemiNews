from databases import Database
import os


DATABASE_URL = os.getenv("DATABASE_URL")
db = Database(DATABASE_URL)

async def connect_db():
    await db.connect()

async def disconnect_db():
    await db.disconnect()
