import os
import logging
import asyncio
from ubisoftparser import get_ubisoft_games_with_discount

from aiogram import Bot

API_TOKEN = os.getenv('API_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
ubisoft_games_with_discount = get_ubisoft_games_with_discount("Anno 1800")


async def send_message(channel_id: int, text: str):
    if len(text) > 4096:
        for x in range(0, len(text), 4096):
            await bot.send_message(channel_id, text[x:x + 4096])
    else:
        await bot.send_message(channel_id, text)


async def main():
    await send_message(CHANNEL_ID, ubisoft_games_with_discount)


if __name__ == '__main__':
    asyncio.run(main())
