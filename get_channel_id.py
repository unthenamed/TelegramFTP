import asyncio
import sys
import logging

# Setup logging untuk debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fix untuk Python 3.14 - setup event loop sebelum import pyrogram
if sys.version_info >= (3, 10):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, idle
from os import environ
from os.path import exists

if exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

# Suppress pyrogram debug logs
logging.getLogger("pyrogram").setLevel(logging.WARNING)

bot = Client(
    "S3_Bot",
    api_id=int(environ.get("API_ID", 0)),
    api_hash=environ.get("API_HASH"),
    bot_token=environ.get("BOT_TOKEN")
)

# Handler untuk SEMUA pesan (tanpa filter)
@bot.on_message()
async def handle_all_messages(client, message):
    try:
        # Log semua pesan yang diterima
        logger.info(f"[RECEIVED] Text: {message.text} | Chat ID: {message.chat.id} | User: {message.from_user.id if message.from_user else 'None'}")
        
        # Skip jika message.text tidak ada
        if not message.text:
            logger.info("[SKIP] No message text")
            return
            
        text = message.text.strip()
        logger.info(f"[PROCESS] Checking message: '{text}'")
        
        # Cek apakah pesan dimulai dengan /id
        if text.startswith("/id"):
            logger.info(f"[ACTION] Detected /id command")
            try:
                response = f"Chat ID: `{message.chat.id}`"
                sent = await message.reply(response, parse_mode="markdown")
                logger.info(f"[SUCCESS] Reply sent with message_id: {sent.id}")
            except Exception as e:
                logger.error(f"[ERROR] Failed to send reply: {e}", exc_info=True)
        
        # Cek apakah pesan dimulai dengan /channel
        elif text.startswith("/channel"):
            logger.info(f"[ACTION] Detected /channel command")
            try:
                response = f"Chat ID: `{message.chat.id}`"
                sent = await message.reply(response, parse_mode="markdown")
                logger.info(f"[SUCCESS] Reply sent with message_id: {sent.id}")
            except Exception as e:
                logger.error(f"[ERROR] Failed to send reply: {e}", exc_info=True)
        
        else:
            logger.info(f"[IGNORE] Message doesn't match any command")
            
    except Exception as e:
        logger.error(f"[CRITICAL] Handler error: {e}", exc_info=True)

async def main():
    try:
        print('Bot starting... Press Ctrl+C to stop.')
        logger.info("=" * 60)
        logger.info("Bot is starting...")
        
        await bot.start()
        logger.info("Bot connected!")
        
        # Print info bot
        me = await bot.get_me()
        logger.info(f"Bot: @{me.username} (ID: {me.id})")
        logger.info("=" * 60)
        logger.info("Bot is listening for messages...")
        logger.info("Send /id or /channel to test")
        logger.info("=" * 60)
        
        await idle()
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        await bot.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
