from datetime import datetime

from sqlalchemy import (JSON, BigInteger, Boolean, DateTime, ForeignKey,
                        Integer, String, Text, func)
from sqlalchemy.orm import mapped_column, relationship
from tg_logger import BaseLogger

from db.base import Base
from db.consts import LENGTH_OF_NAME_FIELDS, LENGTH_OF_STATE
from db.table_names import BOTUSER_TABLE, TGBOT_TABLE

logger = BaseLogger()


class BotUser(Base):
    __tablename__ = BOTUSER_TABLE
    __table_args__ = {'extend_existing': True}

    id = mapped_column(BigInteger, primary_key=True)

    tgbot_id = mapped_column(BigInteger, ForeignKey(f"{TGBOT_TABLE}.id"))
    tgbot = relationship('TGBot', back_populates='bot_users')

    tg_id = mapped_column(BigInteger)
    admin = mapped_column(Boolean, default=False)
    username = mapped_column(String(LENGTH_OF_NAME_FIELDS), nullable=True,
                             default=None)
    first_name = mapped_column(String(LENGTH_OF_NAME_FIELDS), nullable=True,
                               default=None)
    last_name = mapped_column(String(LENGTH_OF_NAME_FIELDS), nullable=True,
                              default=None)
    utm_id = mapped_column(Integer, nullable=True, default=None)
    status = mapped_column(String(LENGTH_OF_NAME_FIELDS), nullable=True,
                           default=None)
    is_channel_subscribed = mapped_column(Boolean, default=False)
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow,
                               onupdate=func.now())
    state = mapped_column(String(LENGTH_OF_STATE), nullable=True, default=None)
    email = mapped_column(Text, nullable=True, default=None)
    dating_answers = mapped_column(JSON, default=dict)

    def __repr__(self):
        return f"BotUser({self.id} / {self.tg_id})"
