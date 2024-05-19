from telethon import events

from tg_bots.state_machine import BotStates
from tg_bots.handlers.base_handlers import BaseHandlers, get_state_checker


class SystemHandlers(BaseHandlers):
    def wait_messages(self, client):
        state_checker = get_state_checker(self, BotStates.menu)

        @client.on(events.NewMessage(incoming=True, pattern='/start'))
        async def start_handler(event):
            chat_id = event.chat_id
            # Регистрация пользователя

            # Приветствие
            await event.reply('Привет! Я бот для заказа товаров. ')