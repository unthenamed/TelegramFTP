import asyncio

# --- TAMBAHKAN BARIS INI ---
# Membuat event loop manual untuk mencegah error Pyrogram di Python 3.12+
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
# ---------------------------

import os
from pyrogram import Client
import aioftp
import aiosqlite
from dotenv import load_dotenv
from loguru import logger
import io

# ... (lanjutkan dengan kode yang sebelumnya di bawah ini) ...

import os
from pyrogram import Client
import aioftp
import aiosqlite
from dotenv import load_dotenv
from loguru import logger
import io

# Memuat konfigurasi dari .env
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
FTP_USER = os.getenv("FTP_USER")
FTP_PASS = os.getenv("FTP_PASS")
FTP_HOST = os.getenv("FTP_HOST", "0.0.0.0")
FTP_PORT = int(os.getenv("FTP_PORT", 9021))

# Inisialisasi Klien Telegram
app = Client("ftp_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ==========================================
# 1. DATABASE MANAGER (SQLite)
# ==========================================
async def init_db():
    """Membuat tabel untuk menyimpan mapping antara path file FTP dan Message ID Telegram."""
    async with aiosqlite.connect("ftp_index.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT UNIQUE NOT NULL,
                message_id INTEGER NOT NULL,
                size INTEGER NOT NULL,
                is_dir BOOLEAN NOT NULL DEFAULT 0
            )
        """)
        await db.commit()
    logger.info("Database SQLite berhasil diinisialisasi.")
# ==========================================
# 2. VIRTUAL FILE SYSTEM (VFS) - REVISED
# ==========================================
class TelegramPath(aioftp.PathIO):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = "ftp_index.db"

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

    async def is_file(self, path):
        return not await self.is_dir(path)

    async def stat(self, path):
        # Mengembalikan metadata yang lebih "ramah" untuk klien FTP
        import time
        class Stat:
            st_size = 0
            st_mtime = time.time()
            st_ctime = time.time()
            st_mode = 0o40755 # Default untuk directory/file standar
        
        if str(path) in (".", "/"):
            return Stat()
            
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT size, is_dir FROM files WHERE filepath = ?", (str(path),)) as cursor:
                row = await cursor.fetchone()
                if not row: raise FileNotFoundError
                
                s = Stat()
                s.st_size = row[0]
                s.st_mode = 0o100644 if not row[1] else 0o40755
                return s

    async def list(self, path):
        # Mengembalikan list file dengan format yang diharapkan klien
        import pathlib
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT filepath FROM files") as cursor:
                async for row in cursor:
                    # Kita harus mengirim path relatif, bukan path absolut
                    yield pathlib.Path(row[0]).name

    # ... (Biarkan fungsi mkdir, rmdir, unlink, open seperti sebelumnya) ...
#==========================================
# 3. SERVER RUNNER
# ==========================================
async def main():
    logger.info("Memulai persiapan server...")
    
    # 1. Inisialisasi Database
    await init_db()
    
    # 2. Start Klien Telegram
    await app.start()
    logger.success("Klien Telegram terhubung!")
    
    # 3. Konfigurasi Autentikasi FTP
    user = aioftp.User(
        login=FTP_USER, 
        password=FTP_PASS, 
        base_path="/", 
        home_path="/"
    )
    
    # 4. Start FTP Server
    # Kita hapus 'passive_ports' untuk menghindari error tipe argumen
    server = aioftp.Server(
        users=[user],
        path_io_factory=TelegramPath
    )
    
    logger.info(f"FTP Server berjalan di {FTP_HOST}:{FTP_PORT}")
    # Jika perlu membatasi koneksi, kita bisa lakukan di luar parameter Server jika diperlukan,
    # namun aioftp biasanya cukup stabil dengan pengaturan standar ini.
    await server.start(FTP_HOST, FTP_PORT)

    
    # Biarkan program berjalan selamanya
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Mematikan server...")
        app.stop()
