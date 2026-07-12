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
# 2. VIRTUAL FILE SYSTEM (VFS)
# ==========================================
class TelegramPath(aioftp.PathIO):
    """
    Sistem File Virtual kustom yang mencegat (intercept) operasi FTP
    dan mengarahkannya ke Telegram dan database lokal.
    """
    
    def __init__(self, path="."):
        super().__init__(path)
        self.db_path = "ftp_index.db"

    async def exists(self):
        if str(self.path) == "." or str(self.path) == "/":
            return True
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id FROM files WHERE filepath = ?", (str(self.path),)) as cursor:
                return await cursor.fetchone() is not None

    async def is_dir(self):
        if str(self.path) == "." or str(self.path) == "/":
            return True
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT is_dir FROM files WHERE filepath = ?", (str(self.path),)) as cursor:
                row = await cursor.fetchone()
                return bool(row[0]) if row else False

    async def is_file(self):
        return not await self.is_dir()

    async def mkdir(self, parents=False, exist_ok=False):
        """Membuat folder virtual di database"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO files (filepath, message_id, size, is_dir) VALUES (?, ?, ?, ?)",
                    (str(self.path), 0, 0, True)
                )
                await db.commit()
                logger.info(f"Folder dibuat: {self.path}")
            except aiosqlite.IntegrityError:
                if not exist_ok:
                    raise FileExistsError

    async def rmdir(self):
        """Menghapus folder virtual"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM files WHERE filepath = ? AND is_dir = 1", (str(self.path),))
            await db.commit()

    async def unlink(self):
        """Menghapus file (menghapus pesan di telegram dan entri DB)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT message_id FROM files WHERE filepath = ?", (str(self.path),)) as cursor:
                row = await cursor.fetchone()
                if row:
                    msg_id = row[0]
                    await app.delete_messages(CHAT_ID, msg_id)
                    await db.execute("DELETE FROM files WHERE filepath = ?", (str(self.path),))
                    await db.commit()
                    logger.info(f"File dihapus: {self.path}")

    async def stat(self):
        """Mengembalikan metadata file ke FTP Client"""
        if str(self.path) == "." or str(self.path) == "/":
            class DummyStat:
                st_size = 0
                st_mtime = 0
                st_ctime = 0
                st_mode = 0o755 | 0o40000 # Mode direktori
            return DummyStat()
            
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT size, is_dir FROM files WHERE filepath = ?", (str(self.path),)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    raise FileNotFoundError
                
                class Stat:
                    st_size = row[0]
                    st_mtime = 0
                    st_ctime = 0
                    # 0o40000 untuk direktori, 0o100000 untuk file reguler
                    st_mode = (0o755 | 0o40000) if row[1] else (0o644 | 0o100000)
                return Stat()

    async def open(self, mode="r", *args, **kwargs):
        """
        Logika inti saat FTP Client mulai mengunggah (w) atau mengunduh (r).
        Catatan: Ini menggunakan pendekatan stream simulasi sederhana.
        """
        if "w" in mode:
            # Mengembalikan stream writer yang nantinya diarahkan ke Pyrogram
            # Pada implementasi VFS penuh, di sini menggunakan Async Generator
            return TelegramFileWriter(str(self.path), self.db_path)
        elif "r" in mode:
            return TelegramFileReader(str(self.path), self.db_path)


# --- Helper Classes untuk Streaming Read/Write ---

class TelegramFileWriter:
    """Buffer untuk menangkap data unggahan dari FTP dan mengirim ke Telegram"""
    def __init__(self, path, db_path):
        self.path = path
        self.db_path = db_path
        self.buffer = io.BytesIO() # Untuk produksi file besar, gunakan Async Queue + Chunking
        
    async def write(self, data):
        self.buffer.write(data)
        
    async def close(self):
        self.buffer.seek(0)
        # Kirim ke Telegram setelah klien FTP selesai mengirim data
        logger.info(f"Mengunggah {self.path} ke Telegram...")
        msg = await app.send_document(
            chat_id=CHAT_ID, 
            document=self.buffer, 
            file_name=os.path.basename(self.path)
        )
        # Simpan Message ID ke Database
        size = self.buffer.getbuffer().nbytes
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO files (filepath, message_id, size, is_dir) VALUES (?, ?, ?, ?)",
                (self.path, msg.id, size, False)
            )
            await db.commit()
        logger.success(f"Berhasil mengunggah: {self.path} (ID: {msg.id})")

class TelegramFileReader:
    """Mengunduh stream data dari Telegram dan mengirimnya ke FTP Client"""
    def __init__(self, path, db_path):
        self.path = path
        self.db_path = db_path
        self.data_stream = None
        
    async def read(self, size=-1):
        if self.data_stream is None:
            # Dapatkan Message ID
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("SELECT message_id FROM files WHERE filepath = ?", (self.path,)) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        raise FileNotFoundError
                    msg_id = row[0]
            
            # Unduh ke memory buffer (Untuk efisiensi tinggi, gunakan stream generator pyrogram)
            logger.info(f"Mengunduh dari Telegram (Msg ID: {msg_id})...")
            self.data_stream = await app.download_media(
                message=msg_id, 
                in_memory=True
            )
            self.data_stream.seek(0)
            
        return self.data_stream.read(size)
        
    async def close(self):
        if self.data_stream:
            self.data_stream.close()

# ==========================================
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
    # Kita menggunakan `path_io_factory` untuk memaksa aioftp menggunakan 
    # VFS kustom (TelegramPath) milik kita.
    server = aioftp.Server(
        users=[user],
        path_io_factory=TelegramPath
    )
    
    logger.info(f"FTP Server berjalan di {FTP_HOST}:{FTP_PORT}")
    await server.start(FTP_HOST, FTP_PORT)
    
    # Biarkan program berjalan selamanya
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Mematikan server...")
        app.stop()
