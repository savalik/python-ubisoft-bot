import os
import logging
import asyncio

import data_access.base
import ubisoftparser
import compare_price

from data_access.game import Game
from data_access.user import User
from ubisoftparser import get_ubisoft_games, get_all_games_by_discount
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters import Text
from aiogram.utils import exceptions

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func

import sys

GOOD_DEAL_PERCENT = 5
GAMES_IN_ONE_MESSAGE = 100
ALL_GAMES = 'ALL-GAMES'


def prepare_message(games_with_good_discount):
    answer = []
    message = f'Games with good discount: {len(games_with_good_discount)}'
    answer.append(message)
    for gameWithDiscount in games_with_good_discount:
        answer.append(gameWithDiscount.print_game())
    return ''.join(answer)


async def send_message(channel_id: int, text: str):
    if len(text) > 4096:
        for x in range(0, len(text), 4096):
            await bot.send_message(channel_id, text[x:x + 4096])
    else:
        await bot.send_message(channel_id, text)


async def main(users, ubisoft_games_with_discount=None):
    if ubisoft_games_with_discount:
        _games = {ubisoftparser.Game.from_parsed(game) for game in ubisoft_games_with_discount}
        for user in users:
            games_for_sending = get_all_games_by_discount(_games, GOOD_DEAL_PERCENT)
            message = prepare_message(games_for_sending)
            await send_message(int(CHANNEL_ID), message)


def check_env_variables():
    if API_TOKEN is None:
        print("API_TOKEN variable are not set")
    if CHANNEL_ID is None:
        print("CHANNEL_ID variable are not set")
    if DB_CONNECTION_STRING is None:
        print("DB_CONNECTION_STRING variable are not set")
    if (API_TOKEN is None) or (CHANNEL_ID is None) or (DB_CONNECTION_STRING is None):
        exit()


if __name__ == '__main__':
    API_TOKEN = os.getenv('API_TOKEN')
    CHANNEL_ID = os.getenv('CHANNEL_ID')
    DB_CONNECTION_STRING = os.getenv('DB_CONNECTION_STRING')

    check_env_variables()

    # Configure logging
    logging.basicConfig(level=logging.DEBUG)

    # Initialize bot and dispatcher
    bot = Bot(token=API_TOKEN)

    engine = create_engine(DB_CONNECTION_STRING)
    data_access.base.Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Here we get all games and save it to DB. Change it to compare with saved data, and save only changed
    fresh_games_list = get_ubisoft_games()
    # fresh_games_list = []

    savedGames = data_access.game.fetch_all_current_prices_from_db(session)
    print(f'{len(savedGames)}  prices was read from db')

    fresh_games_dal = {Game.from_parsed(game) for game in fresh_games_list}
    changed_prices = compare_price.get_changed_prices(savedGames, fresh_games_dal)
    if len(changed_prices) > 0:
        session.bulk_save_objects(changed_prices)
        session.commit()

    print(f'{len(changed_prices)}  prices was updated')

    import sys

    if len(sys.argv) == 2 and sys.argv == 'start-bot':
        dp = Dispatcher(bot)

        @dp.message_handler(commands=['start', 'help'])
        async def send_welcome(message: types.Message):
            greet_kb = ReplyKeyboardMarkup(resize_keyboard=True)
            greet_kb.add(KeyboardButton('Покажи мои настройки!'))\
                .add(KeyboardButton('Подпиши меня на игру!')) \
                .add(KeyboardButton('Отпиши меня от игры!')) \
                .add(KeyboardButton('Покажи все скидки ubisoft!')) \
                .add(KeyboardButton('Покажи мои скидки!'))
            await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.", reply_markup=greet_kb)


        @dp.message_handler(Text(equals="Покажи все скидки ubisoft!"))
        async def send_all_discounts(message: types.Message):
            last_prices = data_access.game.fetch_all_current_prices_from_db(session)
            games_for_sending = get_all_games_by_discount(last_prices, GOOD_DEAL_PERCENT)
            message_for_sending = prepare_message(games_for_sending)
            if len(message_for_sending) > 4096:
                for x in range(0, len(message_for_sending), 4096):
                    await message.reply(message_for_sending[x:x + 4096])
            else:
                await message.reply(message_for_sending)


        @dp.message_handler(Text(equals="Покажи мои настройки!"))
        async def show_user_settings(message: types.Message):
            settings = data_access.user.get_user_settings(session, message.from_user.id)
            if settings is None:
                await message.reply('Нетути настроечек')
            else:
                games_list = settings.games if not settings.all_games else 'все игры'
                msg = f'Вы подписаны на следующие скидки: {games_list}'
                await message.reply(msg)

        # TODO: подписаться на все игры одной кнопкой
        @dp.message_handler(Text(equals="Подпиши меня на игру!"))
        async def subscribe_on_game(message: types.Message):
            _is_first_message = True
            titles_list = data_access.game.fetch_list_of_titles(session)
            if len(titles_list) > GAMES_IN_ONE_MESSAGE:
                for x in range(0, len(titles_list), GAMES_IN_ONE_MESSAGE):
                    titles_kb = InlineKeyboardMarkup()
                    if _is_first_message:
                        titles_kb.add(InlineKeyboardButton('Подпиши меня на все игры', callback_data=f's_{ALL_GAMES}'))
                        _is_first_message = False
                    debug_title_list = []
                    for title in titles_list[x:x + GAMES_IN_ONE_MESSAGE]:
                        title_name = getattr(title, 'title')
                        debug_title_list.append(title_name)
                        cb_data = f's_{title_name}'
                        titles_kb.add(InlineKeyboardButton(title_name, callback_data=cb_data))
                    try:
                        await message.reply('Выбирите игру', reply_markup=titles_kb)
                    except exceptions.ButtonDataInvalid:
                        await message.reply('Произошла ошибка при отправке следующих игр:')
                        await message.reply(' '.join(debug_title_list))

            else:
                titles_kb = InlineKeyboardMarkup()
                titles_kb.add(InlineKeyboardButton('Подписаться на все игры', callback_data=f's_{ALL_GAMES}'))
                for title in titles_list:
                    title_name = getattr(title, 'title')
                    cb_data = f's_{title_name}'
                    titles_kb.add(InlineKeyboardButton(title_name, callback_data=cb_data))
                await message.reply("Первая инлайн кнопка", reply_markup=titles_kb)


        @dp.message_handler(Text(equals="Отпиши меня от игры!"))
        async def unsubscribe_from_game(message: types.Message):
            _is_first_message = True
            settings = data_access.user.get_user_settings(session, message.from_user.id)
            titles_list = settings.games.split('|')
            if len(titles_list) > GAMES_IN_ONE_MESSAGE:
                for x in range(0, len(titles_list), GAMES_IN_ONE_MESSAGE):
                    titles_kb = InlineKeyboardMarkup()
                    if _is_first_message:
                        titles_kb.add(InlineKeyboardButton('Отписаться от всех игр', callback_data=f'u_{ALL_GAMES}'))
                        _is_first_message = False
                    for title in titles_list[x:x + GAMES_IN_ONE_MESSAGE]:
                        cb_data = f'u_{title}'
                        titles_kb.add(InlineKeyboardButton(title, callback_data=cb_data))
                    await message.reply('Выберите игру', reply_markup=titles_kb)
            else:
                titles_kb = InlineKeyboardMarkup()
                titles_kb.add(InlineKeyboardButton('Отписаться от всех игр', callback_data=f'u_{ALL_GAMES}'))
                for title in titles_list:
                    cb_data = f'u_{title}'
                    titles_kb.add(InlineKeyboardButton(title, callback_data=cb_data))
                await message.reply("Выберите игру, от которой вы хотите отписаться", reply_markup=titles_kb)


        @dp.message_handler(Text(equals="Покажи мои скидки!"))
        async def send_user_discounts(message: types.Message):
            settings = data_access.user.get_user_settings(session, message.from_user.id)
            if settings is None:
                await message.reply('Нетути настроечек')
            else:
                last_prices = data_access.game.fetch_all_current_prices_from_db(session)
                if settings.all_games:
                    games_for_sending = get_all_games_by_discount(last_prices, GOOD_DEAL_PERCENT)
                    message_for_sending = prepare_message(games_for_sending)
                    if len(message_for_sending) > 4096:
                        for x in range(0, len(message_for_sending), 4096):
                            await message.reply(message_for_sending[x:x + 4096])
                    else:
                        await message.reply(message_for_sending)
                elif len(settings.games) > 0:
                    games_list = settings.games.split('|')
                    games_for_sending = []
                    for game in games_list:
                        games_for_sending.extend(get_all_games_by_discount(last_prices, GOOD_DEAL_PERCENT, game))
                    message_for_sending = prepare_message(games_for_sending)
                    if len(message_for_sending) > 4096:
                        for x in range(0, len(message_for_sending), 4096):
                            await message.reply(message_for_sending[x:x + 4096])
                    else:
                        await message.reply(message_for_sending)
                else:
                    await message.reply('Вы не подписаны ни на одну игру')


        @dp.callback_query_handler(lambda c: c.data.startswith('s_'))
        async def process_callback_subscribe_button(callback_query: types.CallbackQuery):
            await bot.answer_callback_query(callback_query.id)
            if callback_query.data == f's_{ALL_GAMES}':
                data_access.user.add_all_games_from_user_settings(session, callback_query.from_user.id)
            else:
                data_access.user.add_game_to_user_settings(
                    session,
                    callback_query.from_user.id,
                    callback_query.data.replace('s_', ''))
            await bot.send_message(callback_query.from_user.id, callback_query.data)


        @dp.callback_query_handler(lambda c: c.data.startswith('u_'))
        async def process_callback_unsubscribe_button(callback_query: types.CallbackQuery):
            await bot.answer_callback_query(callback_query.id)
            if callback_query.data == f'u_{ALL_GAMES}':
                data_access.user.remove_all_games_from_user_settings(session, callback_query.from_user.id)
            else:
                data_access.user.remove_game_from_user_settings(
                    session,
                    callback_query.from_user.id,
                    callback_query.data.replace('u_', ''))
            await bot.send_message(callback_query.from_user.id, callback_query.data)


        executor.start_polling(dp, skip_updates=True)

    elif len(sys.argv) == 1:
        if len(changed_prices) > 0:
            asyncio.run(main(changed_prices))
