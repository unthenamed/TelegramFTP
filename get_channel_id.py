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

# Raw update handler
@bot.on_raw_update()
async def raw_update_handler(client, update):
    try:
        logger.info(f"[RAW UPDATE] Type: {type(update).__name__}")
        
        # Cek jika ada UpdateNewMessage
        if hasattr(update, 'message'):
            message = update.message
            logger.info(f"[RAW MESSAGE] Received update with message")
            
            if hasattr(message, 'message') and message.message:
                text = message.message
                logger.info(f"[TEXT] {text}")
                
                if text.startswith("/id"):
                    logger.info(f"[ID DETECTED] Processing /id")
                    chat_id = message.peer_id.user_id if hasattr(message.peer_id, 'user_id') else message.peer_id.channel_id
                    logger.info(f"[CHAT ID] {chat_id}")
                    
                    try:
                        # Send reply
                        await client.send_message(chat_id, f"Chat ID: `{chat_id}`")
                        logger.info(f"[SUCCESS] Reply sent")
                    except Exception as e:
                        logger.error(f"[ERROR] Failed to send: {e}", exc_info=True)
                
                elif text.startswith("/channel"):
                    logger.info(f"[CHANNEL DETECTED] Processing /channel")
                    chat_id = message.peer_id.user_id if hasattr(message.peer_id, 'user_id') else message.peer_id.channel_id
                    logger.info(f"[CHAT ID] {chat_id}")
                    
                    try:
                        # Send reply
                        await client.send_message(chat_id, f"Chat ID: `{chat_id}`")
                        logger.info(f"[SUCCESS] Reply sent")
                    except Exception as e:
                        logger.error(f"[ERROR] Failed to send: {e}", exc_info=True)
                        
    except Exception as e:
        logger.error(f"[ERROR RAW] {e}", exc_info=True)

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
        logger.info("Bot is listening for raw updates...")
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
