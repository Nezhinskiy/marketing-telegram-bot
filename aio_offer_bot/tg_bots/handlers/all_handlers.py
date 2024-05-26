import asyncio
from typing import List

from tg_logger import BaseLogger

from db.models.tgbot import TGBot
from db.session import AsyncSessionType
from tg_bots.handlers.system_handlers import SystemHandlers
from tg_bots.state_machine import RedisStateMachine


class AllHandlers:
    def __init__(
            self,
            tgbot: TGBot,
            tgbot_id: str,
            has_channel: bool,
            async_session: AsyncSessionType,
            admin_list: List[int],
            dating_questions: dict[str, list[str]],
            loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    ):
        self.handlers_list = [
            SystemHandlers,
        ]
        self.tgbot = tgbot
        self.tgbot_id = tgbot_id
        self.loop = loop
        self.has_channel = has_channel
        self.dating_questions = dating_questions
        asyncio.set_event_loop(self.loop)
        self.logger = BaseLogger()
        self.async_session = async_session
        self.state_machine = RedisStateMachine(tgbot, self.async_session)
        self.admin_list = admin_list

    def wait_messages(self, client):
        for handler in self.handlers_list:
            handler(**self.__dict__).wait_messages(client)
