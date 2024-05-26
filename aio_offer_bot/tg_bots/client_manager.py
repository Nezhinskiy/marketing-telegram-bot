from bot_managers import (PatchedTelegramClient, ShuttingDown,
                          TelethonClientManager, TelethonErrorHandler)
from sqlalchemy import and_, select

from config import SESSION_ROOT
from core.proxy import ProxyManager
from db.models.bot_user import BotUser
from db.models.tgbot import TGBot
from db.session import AsyncSessionType, get_session


async def _get_user(
        async_session: AsyncSessionType,
        tg_id: int,
        client: PatchedTelegramClient
) -> BotUser:
    async with async_session() as session:
        senders = await session.filter_by(BotUser, dict(tg_id=tg_id))

    if senders == 1:
        return senders[0]

    tgbot = await client.get_me()
    async with async_session() as session:
        stmt = (
            select(BotUser)
            .join(TGBot.bot_users)
            .where(and_(
                TGBot.tgbot_id == str(tgbot.id),
                BotUser.tg_id == tg_id,
            ))
        )
        cursor = await session.execute(stmt)
        return cursor.scalar()


async def set_user_status(
        tg_id: int,
        client: PatchedTelegramClient,
        status: str
) -> None:
    async_session = get_session()
    user = await _get_user(async_session, tg_id, client)
    async with async_session() as session:
        await session.update(BotUser, dict(id=user.id), dict(status=status))


async def get_user_status(tg_id: int, client: PatchedTelegramClient) -> str:
    async_session = get_session()
    user = await _get_user(async_session, tg_id, client)
    return user.status


TelethonErrorHandler.set_sender_status = set_user_status
TelethonErrorHandler.get_sender_status = get_user_status


class MyTelethonClientManager(TelethonClientManager):
    timeout: int = 2
    try_limit: int = 5
    proxys = ProxyManager()
    ShuttingDownClass = ShuttingDown
    PARSE_CODE_LANG: bool = True
    SESSION_ROOT: str = SESSION_ROOT

    async def _get_str_session(
            self,
            tgbot: TGBot
    ) -> str:
        return tgbot.session

    async def get_tgbot_by_id(self, tgbot_id: TGBot.tgbot_id) -> TGBot:
        async_session = get_session()
        async with async_session() as session:
            result = await session.execute(
                select(TGBot).where(TGBot.tgbot_id == str(tgbot_id))
            )
            return result.scalars().first()
