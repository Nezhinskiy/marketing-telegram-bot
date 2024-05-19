from aiohttp import ClientSession, client_exceptions
from sqlalchemy import update, select

from core.utils import str_exception
from db.session import AsyncSessionType
from loggers import get_logger

from db.models.bot_user import BotUser

logger = get_logger()


class ChannelManager:
    def __init__(self, tgbot=None, bot_user_id=None):
        self.tgbot = tgbot
        self.bot_user = None
        self.bot_user_id = bot_user_id

    async def __get_bot_user(self, async_session: AsyncSessionType):
        if self.bot_user_id is None:
            return
        async with async_session() as session:
            stmt = (
                select(BotUser).where(BotUser.id == self.bot_user_id)
            )
            cursor = await session.execute(stmt)
            return cursor.scalar()

    async def check_via_database(self, async_session: AsyncSessionType):
        self.bot_user = await self.__get_bot_user(async_session)
        return self.bot_user.is_channel_subscribed

    async def _request_tg_sender_status(self):
        api_key = self.tgbot.admin_api_key
        channel = self.tgbot.channel_name
        url = f'https://api.telegram.org/bot{api_key}/getChatMember'
        params = {'chat_id': f'@{channel}', 'user_id': self.bot_user.tg_id}
        async with ClientSession() as session:
            async with session.post(url=url, params=params) as response:
                response.raise_for_status()
                resp_json = await response.json()
                return resp_json['result']['status']

    async def check_via_request(self, async_session: AsyncSessionType) -> bool:
        self.bot_user = await self.__get_sender(async_session)
        is_participant = True
        msg = f'tgbot={self.tgbot.tgbot_id}, sender={self.bot_user.tg_id}:'
        try:
            status = await self._request_tg_sender_status()
        except client_exceptions.ClientResponseError as exc:
            if exc.status == 400:
                logger.check_via_request(
                    'info', f'{msg} Was never a participant'
                )
                is_participant = False
            else:
                logger.check_via_request(
                    'error', f'{msg} Unknown error: ' + str_exception(exc)
                )
                is_participant = True
        except Exception as exc:
            logger.check_via_request('error', msg + str_exception(exc))
            is_participant = True
        else:
            if status in ['left', 'kicked']:
                is_participant = False
            logger.check_via_request('info', f'{msg} {status=}')

        async with async_session() as session:
            await session.execute(
                update(BotUser)
                .values(dict(is_channel_subscribed=is_participant))
                .where(BotUser.id == self.bot_user.id)
            )
            await session.commit()
        return is_participant
