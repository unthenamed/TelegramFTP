import asyncio
import os
import time
import pathlib
import sqlite3
import aioftp
import aiosqlite
from pyrogram import Client
from loguru import logger
from dotenv import load_dotenv

# --- SETUP AWAL ---
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
FTP_HOST = "127.0.0.1"
FTP_PORT = 9090
DB_NAME = "ftp_index.db"

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS files (filepath TEXT UNIQUE, is_dir INTEGER)")
    conn.commit()
    conn.close()

# --- VIRTUAL FILE SYSTEM ---
class TelegramPath(aioftp.PathIO):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = DB_NAME

    async def exists(self, path):
        if str(path) in (".", "/"): return True
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT 1 FROM files WHERE filepath = ?", (str(path),)) as cursor:
                return await cursor.fetchone() is not None

    async def is_dir(self, path):
        if str(path) in (".", "/"): return True
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT is_dir FROM files WHERE filepath = ?", (str(path),)) as cursor:
                row = await cursor.fetchone()
                return bool(row[0]) if row else False

    async def stat(self, path):
        # Struktur stat standar agar klien tidak bingung
        class Stat:
            st_size = 0
            st_mtime = time.time()
            st_mode = 0o40755
            st_nlink = 1
            st_uid = 0
            st_gid = 0
        return Stat()

    async def list(self, path):
        # Mengembalikan objek Path agar aioftp tidak error
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT filepath FROM files") as cursor:
                async for row in cursor:
                    yield pathlib.Path(row[0])

# --- MAIN ---
async def main():
    init_db()
    
    app = Client("ftp_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    await app.start()
    
    # Server Setup
    user = aioftp.User()
    server = aioftp.Server(users=[user], path_io_factory=TelegramPath)
    
    logger.info(f"Server FTP berjalan di {FTP_HOST}:{FTP_PORT}")
    await server.start(FTP_HOST, FTP_PORT)
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
