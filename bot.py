import os
import logging
import asyncio

import data_access.base
import ubisoftparser

from data_access.game import Game
from ubisoftparser import get_ubisoft_games, get_all_games_by_discount
from aiogram import Bot

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

GOOD_DEAL_PERCENT = 45

#API_TOKEN = os.environ.get('API_TOKEN')
CHANNEL_ID = os.environ('CHANNEL_ID')
#DB_CONNECTION_STRING = os.environ('DB_CONNECTION_STRING')
print(CHANNEL_ID)
print(CHANNEL_ID + 1)
#print(os.environ('CHANNEL_ID'))
#print(os.environ('DB_CONNECTION_STRING'))
def prepare_message(games_with_good_discount):
    answer = []
    message = f'Games with good discount: {len(games_with_good_discount)}'
    answer.append(message)
    for gameWithDiscount in games_with_good_discount:
        answer.append(gameWithDiscount.print_game())
    return ''.join(answer)


def get_changed_prices(old_price_array, new_price_array):
    old_prices = {l1.title + l1.sub_title: l1 for l1 in old_price_array}
    new_prices = {l2.title + l2.sub_title: l2 for l2 in new_price_array}
    _changed_prices = []
    for key, value in new_prices.items():
        if key in old_prices:
            old_price = old_prices[key]
            if old_price.price != value.price:
                _changed_prices.append(value)
        else:
            _changed_prices.append(value)
    return _changed_prices


async def send_message(channel_id: int, text: str):
    if len(text) > 4096:
        for x in range(0, len(text), 4096):
            await bot.send_message(channel_id, text[x:x + 4096])
    else:
        await bot.send_message(channel_id, text)


async def main(ubisoft_games_with_discount=None):
    if ubisoft_games_with_discount:
        _games = {ubisoftparser.Game.from_parsed(game) for game in ubisoft_games_with_discount}
        games_for_sending = get_all_games_by_discount(_games, GOOD_DEAL_PERCENT, 'Anno 1800')
        message = prepare_message(games_for_sending)
        await send_message(int(CHANNEL_ID), message)


if __name__ == '__main__':
    API_TOKEN = os.getenv('API_TOKEN')
    CHANNEL_ID = os.getenv('CHANNEL_ID')
    DB_CONNECTION_STRING = os.getenv('DB_CONNECTION_STRING')

    if API_TOKEN is None:
        print("API_TOKEN variable are not set")

    if CHANNEL_ID is None:
        print("CHANNEL_ID variable are not set")

    if DB_CONNECTION_STRING is None:
        print("DB_CONNECTION_STRING variable are not set")

    if (API_TOKEN is None) or (CHANNEL_ID is None) or (DB_CONNECTION_STRING is None):
        exit()

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Initialize bot and dispatcher
    bot = Bot(token=API_TOKEN)

    engine = create_engine(DB_CONNECTION_STRING)
    data_access.base.Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Here we get all games and save it to DB. Change it to compare with saved data, and save only changed
    fresh_games_list = get_ubisoft_games()

    savedGames = session.query(Game).all()
    print(f'{len(savedGames)}  prices was read from db')

    fresh_games_dal = {Game.from_parsed(game) for game in fresh_games_list}
    changed_prices = get_changed_prices(savedGames, fresh_games_dal)
    if len(changed_prices) > 0:
        session.bulk_save_objects(changed_prices)
        session.commit()

    print(f'{len(changed_prices)}  prices was updated')

    if len(changed_prices) > 0:
        asyncio.run(main(changed_prices))
