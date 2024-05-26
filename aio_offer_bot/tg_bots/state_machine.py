import pickle

from sqlalchemy import update
from tg_logger import BaseLogger

from core.redis import create_redis_connection, get_listener_redis_params
from db.models.bot_user import BotUser
from db.models.tgbot import TGBot
from db.session import AsyncSessionType


class BotStates:
    menu = None
    dating = 'dating'
    answer_questions = 'answer'


class RedisStateMachine:

    def __init__(self, tgbot: TGBot, async_session: AsyncSessionType):
        self.logger = BaseLogger()
        self.redis = None
        self.tgbot = tgbot
        self.async_session = async_session

    async def _get_conn(self):
        if not self.redis:
            self.redis = await create_redis_connection(
                *get_listener_redis_params())
        return self.redis

    async def __set_bot_user(
            self,
            bot_user: BotUser,
            bot_user_id: int,
            bot: TGBot
    ) -> None:
        mapping = {
            bot_user_id: pickle.dumps(bot_user)
        }
        redis = await self._get_conn()
        await redis.hset(bot.tgbot_id, mapping=mapping)

    async def __get_bot_user(self, bot_user_id: int, bot: TGBot) -> BotUser:
        redis = await self._get_conn()
        if bot_user := await redis.hget(bot.tgbot_id, bot_user_id):
            return pickle.loads(bot_user)

    async def __has_bot_user(self, bot_user_id: int, bot: TGBot) -> bool:
        redis = await self._get_conn()
        return await redis.hexists(bot.tgbot_id, bot_user_id)

    async def __get_bot_users(self, bot: TGBot):
        redis = await self._get_conn()
        return await redis.hkeys(bot.tgbot_id) or []

    async def set_state(
            self,
            state: str,
            bot: TGBot,
            bot_user: BotUser,
            log_msg: str = 'Changed state'
    ) -> None:
        async with self.async_session() as session:
            stmt = (
                update(BotUser)
                .where(BotUser.id == bot_user.id)
                .values(state=state)
            )
            await session.execute(stmt)
            await session.commit()
        bot_user.state = state
        await self.__set_bot_user(bot_user, bot_user.tg_id, bot)
        self.logger.model_log(
            'info', bot_user, 'update', add_info=log_msg
        )

    async def get_state(self, bot: TGBot, bot_user: BotUser) -> str:
        bot_user_id = bot_user.tg_id
        if not await self.__has_bot_user(bot_user_id, bot):
            await self.__set_bot_user(bot_user, bot_user_id, bot)
        self.logger.model_log('info', bot_user, 'retrieve')
        return bot_user.state

    async def reset_state(
            self,
            bot: TGBot,
            bot_user: BotUser
    ) -> None:
        await self.set_state(BotStates.menu, bot, bot_user, 'Reset state')
