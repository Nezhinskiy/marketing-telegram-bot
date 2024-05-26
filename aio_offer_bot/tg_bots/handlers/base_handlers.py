import asyncio
from abc import abstractmethod
from typing import Any

from telethon.tl import types
from tg_logger import BaseLogger

from db.models.tgbot import TGBot
from db.session import AsyncSessionType
from tg_bots.channel import ChannelManager
from tg_bots.services import (create_dataclass_from_sqlalchemy_obj,
                              get_object_safely)
from tg_bots.state_machine import RedisStateMachine


class BaseHandlers:
    def __init__(
            self,
            tgbot: TGBot,
            tgbot_id: str,
            loop: asyncio.AbstractEventLoop,
            state_machine: RedisStateMachine,
            logger: BaseLogger,
            has_channel: bool,
            async_session: AsyncSessionType,
            admin_list: list[int],
            handlers_list: list['BaseHandlers'],
            dating_questions: dict[str, list[str]]
    ):
        self.handlers_list = handlers_list
        self._tgbot = tgbot
        self.tgbot_data = create_dataclass_from_sqlalchemy_obj(tgbot)
        self.tgbot_id = tgbot_id
        self.dating_questions = dating_questions
        self.loop = loop
        asyncio.set_event_loop(self.loop)
        self.state_machine = state_machine
        self.logger = logger
        self.has_channel = has_channel
        self.async_session = async_session
        self.admin_list = admin_list

    @staticmethod
    def is_text_or_voice_attached(message: types.Message) -> bool:
        return (
            message.message
            or (
                isinstance(message.media, types.MessageMediaDocument)
                and message.media.voice
            )
        )

    @staticmethod
    def is_photo_attached(message: types.Message) -> bool:
        return (
            isinstance(message.media, types.MessageMediaPhoto)
            or (
                isinstance(message.media, types.MessageMediaDocument)
                and not message.media.voice
            )
        )

    async def get_tgbot_safely(self) -> TGBot:
        return await get_object_safely(
            self._tgbot, TGBot, {'tgbot_id': str(self.tgbot_id)},
            self.async_session, self.logger
        )

    @abstractmethod
    def wait_messages(self, client: 'TelegramClient') -> None:
        pass


def get_state_checker(handler: BaseHandlers, accept_state: str) -> Any:
    """
    Возвращает декоратор для проверки стейта, если стейт не совпадает с нужным,
    то хендлер не выполняется.
    Применять только для методов классов хендлеров.
    """
    # def _deco(func):
    #     async def _wrapper(event, *args, **kwargs):
    #         if event.text.startswith('/start'):
    #             return
    #         chat_id = event.chat_id
    #         tgbot = await handler.get_tgbot_safely()
    #         hm = HistoryManager(tgbot, chat_id)
    #         chat_sender = await hm.get_updated_chat_sender(
    #             handler.async_session)
    #         state = await handler.state_machine.get_state(tgbot, chat_sender)
    #         if state != accept_state:
    #             return
    #         return await func(event, *args, **kwargs)
    #     return _wrapper
    # return _deco


def get_channel_checker(handler: BaseHandlers) -> Any:
    def _deco(func):
        async def _wrapper(event, *args, **kwargs):
            if not handler.has_channel:
                return await func(event, *args, **kwargs)
            chat_id = event.chat_id
            tgbot = await handler.get_tgbot_safely()
            cm = ChannelManager(tgbot, chat_id)
            is_participant = (
                await cm.check_via_database(handler.async_session)
                or await cm.check_via_request(handler.async_session)
            )
            if not is_participant:
                await event.respond(
                    # handler.messages.add_users_to_channel_msg,
                    # buttons=subscribe_keyboard(handler.buttons)
                )
                return
            return await func(event, *args, **kwargs)
        return _wrapper
    return _deco
