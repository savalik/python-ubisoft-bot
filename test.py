import datetime
from decimal import Decimal
from dataclasses import dataclass

# TODO: make some unit tests
@dataclass()
class Game:
    title: str
    sub_title: str
    price: Decimal
    discount: Decimal
    updated_on: datetime


def get_changed_prices(old_prices: dict, new_prices: dict):
    _changed_prices = []
    for key, value in new_prices.items():
        old_price = old_prices[key]
        if old_price.price != value.price:
            _changed_prices.append(value)
    return _changed_prices


if __name__ == '__main__':
    g1_1 = Game("game1", "part 1", Decimal(50), Decimal(50), datetime.datetime(2020, 5, 17))
    g2_1 = Game("game2", "part 1", Decimal(10), Decimal(33), datetime.datetime(2020, 5, 17))
    g3_1 = Game("game3", "ult 1", Decimal(10), Decimal(33), datetime.datetime(2020, 5, 17))
    g1_2 = Game("game1", "part 1", Decimal(10), Decimal(90), datetime.datetime(2020, 6, 17))
    g2_2 = Game("game2", "part 1", Decimal(30), Decimal(0), datetime.datetime(2020, 6, 17))
    g3_2 = Game("game3", "ult 1", Decimal(10), Decimal(33), datetime.datetime(2020, 6, 17))

    l1s = [g1_1, g2_1, g3_1]
    l2s = [g1_2, g2_2, g3_2]

    dict_mas1 = {l1.title + l1.sub_title: l1 for l1 in l1s}
    dict_mas2 = {l2.title + l2.sub_title: l2 for l2 in l2s}
    print(dict_mas1, '\n', dict_mas2)

    changed_prices = get_changed_prices(dict_mas1, dict_mas2)
    print(changed_prices)


    # как в этом месте сделать два словаря, где ключем будет конкатенация title и sub_title а значением весь объект game?
