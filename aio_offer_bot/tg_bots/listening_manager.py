from typing import List

from bot_managers import ListeningTGBotManager

from db.models import TGBot
from db.models.bot_user import BotUser
from db.session import AsyncSessionType, get_session
from tg_bots.client_manager import MyTelethonClientManager
from tg_bots.handlers.all_handlers import AllHandlers
from tg_bots.services import get_dating_questions_dict


class MyListeningTGBotManager(ListeningTGBotManager):
    client_class = MyTelethonClientManager
    rabbitmq_enabled: bool = False

    def __init__(
            self,
            admin_list: List[BotUser],
            tgbot_list: List[TGBot],
            **kwargs
    ):
        super().__init__(tgbot_list, **kwargs)
        self.admin_list = admin_list
        self.async_session = get_session()

    async def wait_messages(
            self,
            tgbot: TGBot,
            tgbot_id: int,
            client: MyTelethonClientManager
    ) -> None:
        dating_questions = await get_dating_questions_dict(self.async_session, tgbot)
        has_channel = True if tgbot.channel_name else False


        handlers = AllHandlers(
            tgbot,
            tgbot_id,
            loop=self.loop,
            has_channel=has_channel,
            async_session=self.async_session,
            admin_list=self.admin_list,
            dating_questions=dating_questions
        )
        self.logger.wait_messages('info', tgbot_id)
        handlers.wait_messages(client)
