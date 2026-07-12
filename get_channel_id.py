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

@bot.on_message(filters.text)
async def get_id(_cl, message):
    logger.info(f"Message received: {message.text} from {message.from_user.first_name if message.from_user else 'Unknown'}")
    if message.text.startswith("/id") or message.text.startswith("/channel"):
        logger.info(f"Sending channel ID: {message.chat.id}")
        await message.reply(str(message.chat.id))
    else:
        logger.info(f"Message does not match filter: {message.text}")

async def main():
    try:
        print('Bot starting... Press Ctrl+C to stop.')
        logger.info("Bot is starting...")
        await bot.start()
        logger.info("Bot started successfully!")
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\nBot stopped.")
        logger.info("Bot stopped by user.")
        await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")
