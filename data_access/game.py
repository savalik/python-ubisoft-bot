from sqlalchemy import *
from data_access.base import Base
from datetime import datetime
import ubisoftparser


class Game(Base):
    __tablename__ = 'ubisoft_prices'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(UnicodeText)
    sub_title = Column(UnicodeText, nullable=True)
    price = Column(DECIMAL)
    discount = Column(DECIMAL)
    updated_on = Column(DateTime)

    def __init__(self, title: str, sub_title: str, price: DECIMAL, discount: DECIMAL, updated_on: datetime):
        self.title = title
        self.sub_title = sub_title
        self.price = price
        self.discount = discount
        self.updated_on = updated_on

    @classmethod
    def from_parsed(cls, game: ubisoftparser.Game):
        return cls(game.title, game.sub_title, game.price, game.discount, game.updated_on)


def fetch_all_current_prices_from_db(session):
    subquery = (session.query(
        Game.title,
        Game.sub_title,
        func.max(Game.updated_on)
    ).
                group_by(Game.title, Game.sub_title)
                ).subquery()

    last_prices_dal = session.query(Game).join(subquery, (subquery.c.title == Game.title) & (
            subquery.c.sub_title == Game.sub_title) & (subquery.c.max == Game.updated_on)).all()
    return {ubisoftparser.Game.from_parsed(game) for game in last_prices_dal}


def fetch_list_of_titles(session):
    return session.query(Game.title).distinct().order_by(Game.title).all()
