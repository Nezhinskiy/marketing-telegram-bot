from datetime import datetime

from sqlalchemy import (BigInteger, Boolean, DateTime, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import mapped_column, relationship

from db.base import Base
from db.consts import (LENGTH_OF_API_HASH, LENGTH_OF_API_ID, LENGTH_OF_API_KEY,
                       LENGTH_OF_BUTTON_FIELD, LENGTH_OF_MESSAGE,
                       LENGTH_OF_NAME_FIELDS, LENGTH_OF_SESSION)
from db.table_names import (BOTUSER_TABLE, DATINGQUESTION_TABLE, TGBOT_TABLE,
                            USER_TABLE)


class User(Base):
    __tablename__ = USER_TABLE
    __table_args__ = {'extend_existing': True}

    id = mapped_column(BigInteger, primary_key=True)
    email = mapped_column(String(254))
    username = mapped_column(String(150))
    password = mapped_column(String(150))
    is_superuser = mapped_column(Boolean, default=False)
    first_name = mapped_column(String(150), default='')
    last_name = mapped_column(String(150), default='')
    is_staff = mapped_column(Boolean, default=False)
    is_active = mapped_column(Boolean, default=True)
    membership = mapped_column(Boolean, default=True)

    last_login = mapped_column(DateTime, nullable=True, default=None)
    date_joined = mapped_column(DateTime, default=datetime.utcnow)


class TGBot(Base):
    __tablename__ = TGBOT_TABLE
    __table_args__ = {'extend_existing': True}

    id = mapped_column(BigInteger, primary_key=True)

    bot_users = relationship('BotUser', back_populates='tgbot')

    user_id = mapped_column(BigInteger, ForeignKey(f"{USER_TABLE}.id"))
    user = relationship('User')

    dating_questions = relationship(
        'DatingQuestion', back_populates='tgbot'
    )

    api_id = mapped_column(String(LENGTH_OF_API_ID))
    api_hash = mapped_column(String(LENGTH_OF_API_HASH))
    api_key = mapped_column(String(LENGTH_OF_API_KEY))
    session = mapped_column(String(LENGTH_OF_SESSION))

    welcome_message = mapped_column(Text)
    welcome_photo = mapped_column(Text, nullable=True, default=None)
    info_msg = mapped_column(Text)
    info_button = mapped_column(String(LENGTH_OF_BUTTON_FIELD), default='')
    lead_magnet_msg = mapped_column(Text)
    lead_magnet_photo = mapped_column(Text, nullable=True, default=None)
    lead_magnet_button = mapped_column(String(LENGTH_OF_BUTTON_FIELD), default='')
    dating_success_msg = mapped_column(Text)
    dating_button = mapped_column(String(LENGTH_OF_BUTTON_FIELD), default='')

    name = mapped_column(
        String(LENGTH_OF_NAME_FIELDS), nullable=True, default=None)
    surname = mapped_column(
        String(LENGTH_OF_NAME_FIELDS), nullable=True, default=None)

    tg_username = mapped_column(
        String(LENGTH_OF_NAME_FIELDS), nullable=True, default=None)

    is_activated = mapped_column(Boolean, default=False)

    tgbot_id = mapped_column(String(256), default='')

    archived = mapped_column(Boolean, default=False)

    channel_name = mapped_column(
        String(LENGTH_OF_NAME_FIELDS), nullable=True, default=None)

    admin_api_key = mapped_column(
        String(LENGTH_OF_NAME_FIELDS), nullable=True, default=None)

    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow,
                               onupdate=datetime.utcnow)
    started_at = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"TGBot({self.id} / {self.tgbot_id})"


class DatingQuestion(Base):
    __tablename__ = DATINGQUESTION_TABLE
    __table_args__ = {'extend_existing': True}

    id = mapped_column(BigInteger, primary_key=True)

    tgbot_id = mapped_column(
        BigInteger,
        ForeignKey(f"{TGBOT_TABLE}.id"),
    )
    tgbot = relationship('TGBot', back_populates='dating_questions')

    question = mapped_column(String(LENGTH_OF_MESSAGE), default='')
    answers = mapped_column(ARRAY(String), default=list)
    position = mapped_column(Integer, default=0)
