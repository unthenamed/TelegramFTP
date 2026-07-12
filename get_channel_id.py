import asyncio
import sys

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
    if message.text.startswith("/id") or message.text.startswith("/channel"):
        await message.reply(str(message.chat.id))

async def main():
    try:
        print('Press Ctrl+C to stop.')
        await bot.start()
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("\nBot stopped.")
        await bot.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")
