import os
import logging
import asyncio
from ubisoftparser import get_ubisoft_games_with_discount

from aiogram import Bot


async def send_message(channel_id: int, text: str):
    if len(text) > 4096:
        for x in range(0, len(text), 4096):
            await bot.send_message(channel_id, text[x:x + 4096])
    else:
        await bot.send_message(channel_id, text)


async def main():
    await send_message(int(CHANNEL_ID), ubisoft_games_with_discount)


if __name__ == '__main__':
    API_TOKEN = os.getenv('API_TOKEN')
    CHANNEL_ID = os.getenv('CHANNEL_ID')

    if API_TOKEN is None:
        print("API_TOKEN variable are not set")

    if CHANNEL_ID is None:
        print("CHANNEL_ID variable are not set")

    if(API_TOKEN is None) or (CHANNEL_ID is None):
        exit()

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize bot and dispatcher
    bot = Bot(token=API_TOKEN)
    ubisoft_games_with_discount = get_ubisoft_games_with_discount("Anno 1800")

    asyncio.run(main())
