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

from pyrogram import Client, filters
from os import environ
from os.path import exists

if exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

bot = Client(
    "S3_Bot",
    api_id=int(environ.get("API_ID", 0)),
    api_hash=environ.get("API_HASH"),
    bot_token=environ.get("BOT_TOKEN")
)

# Handler untuk semua message - untuk debug
@bot.on_message()
async def handle_all_messages(client, message):
    logger.info(f"[ALL MESSAGES] Received: {message.text} from {message.from_user.first_name if message.from_user else 'Unknown'} in {message.chat.id}")

# Handler khusus untuk /id dan /channel
@bot.on_message(filters.text & (filters.command("id") | filters.command("channel")))
async def get_id(client, message):
    logger.info(f"[ID COMMAND] Processing /id or /channel from {message.from_user.first_name if message.from_user else 'Unknown'}")
    try:
        await message.reply(f"Channel ID: {message.chat.id}")
        logger.info(f"[ID COMMAND] Reply sent successfully!")
    except Exception as e:
        logger.error(f"[ID COMMAND] Error sending reply: {e}")

async def main():
    try:
        print('Bot starting... Press Ctrl+C to stop.')
        logger.info("Bot is starting...")
        await bot.start()
        logger.info("Bot started successfully!")
        
        # Print info bot
        me = await bot.get_me()
        logger.info(f"Bot username: @{me.username}")
        logger.info(f"Bot ID: {me.id}")
        logger.info(f"Bot first name: {me.first_name}")
        
        logger.info("Waiting for messages...")
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\nBot stopped.")
        logger.info("Bot stopped by user.")
        await bot.stop()
    except Exception as e:
        logger.error(f"Error: {e}")
        await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")
