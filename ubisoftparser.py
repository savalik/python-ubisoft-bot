import re
import requests
from datetime import datetime
from decimal import *
from bs4 import BeautifulSoup

GOOD_DEAL_PERCENT = 45
CHUNK_SIZE = 50
MAX_GAMES = 1000


class Game:
    def __init__(self, title: str, sub_title: str, price: str, discount: str, updated_on: datetime):
        self.title = title
        self.sub_title = sub_title
        prices = re.findall(r'(?:\d+\.)?\d+', price.replace('.', '').replace(',', '.'))
        if len(prices) > 0:
            self.price = Decimal(prices[0])
        else:
            self.price = Decimal(0.0)
        discounts = re.findall("\d+", discount.replace('.', '').replace(',', '.'))
        if len(discounts) > 0:
            self.discount = Decimal(discounts[0])
        else:
            self.discount = Decimal(0.0)
        self.updated_on = updated_on

    def print_game(self):
        message = f'''
        Title: {self.title} {self.sub_title}
        Discount: {self.discount}
        Price: {self.price}\n'''
        return message


def get_all_games_by_discount(li, discount, name=None):
    return [game for game in li if
            game.discount > discount
            and ((name is None) or (name in game.title))]


def get_soup_from_web_page(url, chunk_size, start_position):
    print(f'Make request: {url} size={chunk_size} start position={start_position}')
    params = dict(sz=chunk_size, format='page-element', start=start_position)
    res = requests.get(url, params)
    soup = BeautifulSoup(res.content, 'lxml')
    return soup


def get_games_tiles_from_page_soup(soup):
    games = []
    updated_on = datetime.now()
    tiles = soup.findAll('li', class_='grid-tile cell shrink')
    tiles_count = 0
    price = 0
    for tile in tiles:
        tiles_count += 1
        price_wrappers = tile.findAll('div', class_='price-wrapper')
        pw_count = 0
        discount = ''
        for price_wrapper in price_wrappers:
            pw_count += 1
            if pw_count == 2:
                discount = price
                price = price_wrapper.find('span', class_="price-sales standard-price").text.strip('\n')
            else:
                price = price_wrapper.text.strip('\n')

        card_title = tile.find('div', class_='prod-title')
        if card_title is not None:
            card_title = card_title.text.strip('\n').strip(' ')
        else:
            card_title = ''

        card_sub_title = tile.find('div', class_='card-subtitle')
        if card_sub_title is not None:
            card_sub_title = card_sub_title.text.strip('\n').strip(' ')
        else:
            card_sub_title = ''

        if type(price) is str:
            game = Game(card_title, card_sub_title, price, discount, updated_on)
            games.append(game)
    return games


def get_all_games_from_web_page(url):
    games = []
    while True:
        soup = get_soup_from_web_page(url, CHUNK_SIZE, len(games))
        games_chunk = get_games_tiles_from_page_soup(soup)
        if len(games_chunk) < CHUNK_SIZE:
            games.extend(games_chunk)
            return games
        if len(games) > MAX_GAMES:
            break
        games.extend(games_chunk)
    return games


def get_ubisoft_games():
    return get_all_games_from_web_page("https://store.ubi.com/ru/games")


if __name__ == '__main__':
    fresh_games = get_ubisoft_games()
    print(f'Total games: {len(fresh_games)}')
    for fresh_game in fresh_games:
        print(fresh_game.print_game())
