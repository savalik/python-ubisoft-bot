import requests
from bs4 import BeautifulSoup

GOOD_DEAL_PERCENT = 49
CHUNK_SIZE = 50
MAX_GAMES = 1000


class Game:
    def __init__(self, title, sub_title, price, discount):
        self.title = title
        self.sub_title = sub_title
        self.price = price
        self.discount = discount

    def print_game(self):
        message = f'''
        Title: {self.title} {self.sub_title}
        Discount: {self.discount}
        Price: {self.price}\n'''
        return message


def get_all_games_by_discount(li, discount, name=None):
    return [game for game in li if
            game.discount != 0
            and ((name is None) or (name in game.title))
            and game.discount != ''
            and int(game.discount.strip('%')) * -1 > discount]


def get_soup_from_web_page(url, chunk_size, start_position):
    print(f'Make request: {url} size={chunk_size} start position={start_position}')
    params = dict(sz=chunk_size, format='page-element', start=start_position)
    res = requests.get(url, params)
    soup = BeautifulSoup(res.content, 'lxml')
    return soup


def get_games_tiles_from_page_soup(soup):
    games = []
    tiles = soup.findAll('li', class_='grid-tile cell shrink')
    tiles_count = 0
    price = 0
    for tile in tiles:
        tiles_count += 1
        price_wrappers = tile.findAll('div', class_='price-wrapper')
        pw_count = 0
        discount = 0
        for price_wrapper in price_wrappers:
            pw_count += 1
            if pw_count == 2:
                discount = price
                price = price_wrapper.find('span', class_="price-sales standard-price").text.strip('\n')
            else:
                price = price_wrapper.text.strip('\n')

        card_title = tile.find('h2').text.strip('\n').strip(' ')
        card_sub_title = tile.find('h3').text

        game = Game(card_title, card_sub_title, price, discount)
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


def get_ubisoft_games_with_discount(search_for_name):
    games = get_all_games_from_web_page("https://store.ubi.com/ru/games")
    print(f'Total games: {len(games)}')

    games_with_good_discount = get_all_games_by_discount(games, GOOD_DEAL_PERCENT, search_for_name)
    answer = []
    message = f'Games with good discount: {len(games_with_good_discount)}'
    answer.append(message)
    for gameWithDiscount in games_with_good_discount:
        answer.append(gameWithDiscount.print_game())
    return ''.join(answer)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        get_ubisoft_games_with_discount(sys.argv[1])
    else:
        get_ubisoft_games_with_discount(None)
