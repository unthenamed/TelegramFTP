#!/usr/bin/env python3
"""
Simple Telegram Bot untuk mendapatkan Chat ID
Menggunakan telethon library
"""

import asyncio
import logging
from telethon import TelegramClient, events
from os import environ
from os.path import exists

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
if exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

# Get credentials from environment
API_ID = int(environ.get("API_ID", 0))
API_HASH = environ.get("API_HASH")
BOT_TOKEN = environ.get("BOT_TOKEN")

if not all([API_ID, API_HASH, BOT_TOKEN]):
    logger.error("Missing required environment variables: API_ID, API_HASH, or BOT_TOKEN")
    exit(1)

# Create Telegram client
client = TelegramClient('bot_session', API_ID, API_HASH)

async def main():
    """Main function"""
    try:
        # Start client with bot token
        logger.info("Starting bot...")
        await client.start(bot_token=BOT_TOKEN)
        
        # Get bot info
        me = await client.get_me()
        logger.info(f"Bot started: @{me.username} (ID: {me.id})")
        logger.info("=" * 60)
        logger.info("Bot is listening for messages...")
        logger.info("Send /id or /channel to get chat ID")
        logger.info("=" * 60)
        
        # Message handler
        @client.on(events.NewMessage)
        async def handler(event):
            """Handle new messages"""
            try:
                message_text = event.message.message or ""
                chat_id = event.chat_id
                sender_id = event.sender_id
                
                logger.info(f"[MESSAGE] Text: '{message_text}' | Chat ID: {chat_id} | Sender: {sender_id}")
                
                # Process /id command
                if message_text.strip().startswith("/id"):
                    logger.info(f"[ACTION] Detected /id command")
                    try:
                        response = f"Chat ID: `{chat_id}`"
                        await event.reply(response, parse_mode='markdown')
                        logger.info(f"[SUCCESS] Reply sent to chat {chat_id}")
                    except Exception as e:
                        logger.error(f"[ERROR] Failed to send reply: {e}", exc_info=True)
                
                # Process /channel command
                elif message_text.strip().startswith("/channel"):
                    logger.info(f"[ACTION] Detected /channel command")
                    try:
                        response = f"Chat ID: `{chat_id}`"
                        await event.reply(response, parse_mode='markdown')
                        logger.info(f"[SUCCESS] Reply sent to chat {chat_id}")
                    except Exception as e:
                        logger.error(f"[ERROR] Failed to send reply: {e}", exc_info=True)
                
                else:
                    logger.debug(f"[SKIP] Message doesn't match any command")
                    
            except Exception as e:
                logger.error(f"[CRITICAL] Handler error: {e}", exc_info=True)
        
        # Keep bot running
        logger.info("Bot is now running. Press Ctrl+C to stop.")
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown")
