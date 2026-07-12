import asyncio
import os
import sys
import time
import pathlib
import sqlite3
import threading

# 1. FIX: Setup Event Loop SEBELUM mengimpor library apapun
try:
    asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# 2. Impor Library
from pyrogram import Client
import aioftp
import aiosqlite
from loguru import logger
from dotenv import load_dotenv

# Load Env
load_dotenv()
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID") or 0)
FTP_HOST = "127.0.0.1"
FTP_PORT = 9090
DB_NAME = "ftp_index.db"

# Setup Database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT UNIQUE,
            message_id INTEGER,
            size INTEGER,
            is_dir INTEGER
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database SQLite berhasil diinisialisasi.")

# 3. Virtual File System
class TelegramPath(aioftp.PathIO):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = DB_NAME

    async def exists(self, path):
        if str(path) in (".", "/"): return True
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM files WHERE filepath = ?", (str(path),)) as cursor:
                return await cursor.fetchone() is not None

    async def is_dir(self, path):
        if str(path) in (".", "/"): return True
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT is_dir FROM files WHERE filepath = ?", (str(path),)) as cursor:
                row = await cursor.fetchone()
                return bool(row[0]) if row else False

    async def stat(self, path):
        class Stat:
            st_size = 0
            st_mtime = time.time()
            st_mode = 0o40755
            st_nlink = 1
            st_uid = 0
            st_gid = 0
        
        if str(path) in (".", "/"): return Stat()
            
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT size, is_dir FROM files WHERE filepath = ?", (str(path),)) as cursor:
                row = await cursor.fetchone()
                if not row: raise FileNotFoundError
                
                s = Stat()
                s.st_size = row[0]
                s.st_mode = 0o100644 if not row[1] else 0o40755
                return s

    async def list(self, path):
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT filepath FROM files") as cursor:
                async for row in cursor:
                    # FIX: Harus mengembalikan objek Path, bukan string
                    yield pathlib.Path(row[0])

    async def mkdir(self, path, parents=False, exist_ok=False):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO files (filepath, message_id, size, is_dir) VALUES (?, ?, ?, ?)",
                            (str(path), 0, 0, 1))
            await db.commit()

# 4. Main Program
async def main():
    init_db()
    
    app = Client("ftp_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    await app.start()
    logger.success("Klien Telegram terhubung!")

    user = aioftp.User()
    server = aioftp.Server(
        users=[user],
        path_io_factory=TelegramPath
    )
    
    logger.info(f"FTP Server berjalan di {FTP_HOST}:{FTP_PORT}")
    await server.start(FTP_HOST, FTP_PORT)
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server dihentikan.")
