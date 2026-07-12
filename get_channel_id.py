import asyncio
import sys
import logging

# Setup logging untuk debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
    no_updates=False  # Ensure we receive updates
)

# Handler untuk /id command
@bot.on_message(filters.command("id"))
async def get_id(client, message):
    logger.info(f"[ID COMMAND] Received /id from user {message.from_user.id if message.from_user else 'Unknown'}")
    logger.info(f"[ID COMMAND] Chat ID: {message.chat.id}")
    try:
        response = f"Channel/Chat ID: `{message.chat.id}`"
        await message.reply(response)
        logger.info(f"[ID COMMAND] Reply sent successfully!")
    except Exception as e:
        logger.error(f"[ID COMMAND] Error sending reply: {e}", exc_info=True)

# Handler untuk /channel command
@bot.on_message(filters.command("channel"))
async def get_channel(client, message):
    logger.info(f"[CHANNEL COMMAND] Received /channel from user {message.from_user.id if message.from_user else 'Unknown'}")
    logger.info(f"[CHANNEL COMMAND] Chat ID: {message.chat.id}")
    try:
        response = f"Channel/Chat ID: `{message.chat.id}`"
        await message.reply(response)
        logger.info(f"[CHANNEL COMMAND] Reply sent successfully!")
    except Exception as e:
        logger.error(f"[CHANNEL COMMAND] Error sending reply: {e}", exc_info=True)

# Handler untuk semua pesan (untuk debug)
@bot.on_message()
async def debug_all_messages(client, message):
    logger.debug(f"[DEBUG] Message received: '{message.text}' from {message.from_user.id if message.from_user else 'Unknown'} in chat {message.chat.id}")

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
