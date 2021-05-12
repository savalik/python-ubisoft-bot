from sqlalchemy import *
from data_access.base import Base
from datetime import datetime
from dataclasses import dataclass


@dataclass
class User(Base):
    id: int
    channel_id: int
    games: str
    all_games: bool
    updated_on: datetime
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer)
    games = Column(UnicodeText, nullable=True)
    updated_on = Column(DateTime)
    all_games = Column(Boolean, nullable=False, default=False)


def get_user_settings(session, user_id):
    return session.query(User).where(User.channel_id == user_id).first()


def add_game_to_user_settings(session, user_id, game):
    settings = session.query(User).where(User.channel_id == user_id).first()
    if settings is None:
        new_settings = User(channel_id=user_id, games=game)
        session.add(new_settings)
    else:
        settings.games = settings.games + '|' + game
        settings.games = settings.games.strip('|')
    session.commit()


def remove_game_from_user_settings(session, user_id, game):
    settings = session.query(User).where(User.channel_id == user_id).first()
    if settings is not None:
        settings.games = settings.games.replace(game, '').replace('||', '|').strip('|')
    session.commit()


def remove_all_games_from_user_settings(session, user_id):
    settings = session.query(User).where(User.channel_id == user_id).first()
    if settings is not None:
        settings.games = ''
        settings.all_games = False
    session.commit()


def add_all_games_from_user_settings(session, user_id):
    settings = session.query(User).where(User.channel_id == user_id).first()
    if settings is not None:
        settings.games = ''
        settings.all_games = True
    session.commit()
