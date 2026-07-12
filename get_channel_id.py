import asyncio
import sys
import logging

# Setup logging untuk debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fix untuk Python 3.14 - setup event loop sebelum import pyrogram
if sys.version_info >= (3, 10):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters, idle
from os import environ
from os.path import exists

if exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

bot = Client(
    "S3_Bot",
    api_id=int(environ.get("API_ID", 0)),
    api_hash=environ.get("API_HASH"),
    bot_token=environ.get("BOT_TOKEN"),
    no_updates=False
)

# Handler untuk semua pesan text
@bot.on_message(filters.text)
async def handle_message(client, message):
    text = message.text.strip() if message.text else ""
    logger.info(f"[MESSAGE] Received: '{text}' from {message.from_user.id if message.from_user else 'Unknown'} in chat {message.chat.id}")
    
    # Cek apakah pesan dimulai dengan /id
    if text.startswith("/id"):
        logger.info(f"[ID COMMAND] Processing /id command")
        try:
            response = f"Chat ID: `{message.chat.id}`"
            await message.reply(response, parse_mode="markdown")
            logger.info(f"[ID COMMAND] Reply sent successfully!")
        except Exception as e:
            logger.error(f"[ID COMMAND] Error sending reply: {e}", exc_info=True)
    
    # Cek apakah pesan dimulai dengan /channel
    elif text.startswith("/channel"):
        logger.info(f"[CHANNEL COMMAND] Processing /channel command")
        try:
            response = f"Chat ID: `{message.chat.id}`"
            await message.reply(response, parse_mode="markdown")
            logger.info(f"[CHANNEL COMMAND] Reply sent successfully!")
        except Exception as e:
            logger.error(f"[CHANNEL COMMAND] Error sending reply: {e}", exc_info=True)

async def main():
    try:
        print('Bot starting... Press Ctrl+C to stop.')
        logger.info("=" * 50)
        logger.info("Bot is starting...")
        await bot.start()
        logger.info("Bot started successfully!")
        
        # Print info bot
        me = await bot.get_me()
        logger.info(f"Bot username: @{me.username}")
        logger.info(f"Bot ID: {me.id}")
        logger.info(f"Bot first name: {me.first_name}")
        logger.info("=" * 50)
        
        logger.info("Bot is now listening for messages...")
        logger.info("Send /id or /channel to get chat ID")
        logger.info("=" * 50)
        
        await idle()
        
    except KeyboardInterrupt:
        print("\nBot stopped.")
        logger.info("Bot stopped by user.")
        await bot.stop()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        try:
            await bot.stop()
        except:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")
