import re

from sqlalchemy import update
from telethon import events

from db.consts import EMAIL_REGEX
from db.models.bot_user import BotUser
from db.session import QueryAsyncSession
from tg_bots.handlers.base_handlers import BaseHandlers, get_state_checker
from tg_bots.keyboards.keyboards import (get_answers_keyboard,
                                         get_dating_keyboard,
                                         get_info_keyboard,
                                         get_lead_magnet_keyboard,
                                         get_menu_keyboard)
from tg_bots.state_machine import BotStates


class SystemHandlers(BaseHandlers):
    async def get_user(self, tg_id, tgbot):
        async with self.async_session() as session:
            return await session.first(
                BotUser, dict(tg_id=tg_id, tgbot_id=tgbot.id)
            )

    async def is_user_exist(
        self,
        session: QueryAsyncSession,
        tg_id, tgbot
    ) -> BotUser | bool:
        user = (await session.filter_by(
            BotUser, dict(tg_id=tg_id, tgbot_id=tgbot.id)
        ))[0]
        return user or False

    async def save_new_user(self, event, tgbot):
        chat_id = event.chat_id
        async with self.async_session() as session:
            print('session type:', type(session))
            if user := await self.is_user_exist(session, chat_id, tgbot):
                await self.state_machine.reset_state(tgbot, user)
                return
            utm_id = (
                int(event.text.split()[-1]) if event.text.split()[-1].isdigit()
                else None
            )
            sender = await event.get_sender()
            new_user = BotUser(
                tg_id=sender.id,
                tgbot_id=tgbot.id,
                first_name=sender.first_name,
                last_name=sender.last_name,
                username=sender.username,
                utm_id=utm_id
            )
            session.add(new_user)
            await session.commit()

    async def reset_user_answers(self, user):
        async with self.async_session() as session:
            stmt = (
                update(BotUser)
                .where(BotUser.id == user.id)
                .values(dating_answers=dict())
            )
            await session.execute(stmt)
            await session.commit()

    async def save_user_button_answer(self, user, question_idx, answer_idx):
        user_answers = user.dating_answers
        question = self.dating_questions[question_idx]['question']
        answer = self.dating_questions[question_idx]['answers'][answer_idx]
        async with self.async_session() as session:
            user_answers[question] = answer
            stmt = (
                update(BotUser)
                .where(BotUser.id == user.id)
                .values(dating_answers=user_answers)
            )
            await session.execute(stmt)
            await session.commit()
        return user_answers

    async def save_user_hand_write_answer(self, user, question_idx, answer):
        user_answers = user.dating_answers
        question = self.dating_questions[question_idx]['question']
        email_match = re.search(EMAIL_REGEX, answer)
        email = email_match.group(0) if email_match else None
        async with self.async_session() as session:
            user_answers[question] = answer
            stmt = (
                update(BotUser)
                .where(BotUser.id == user.id)
                .values(dating_answers=user_answers, email=email)
            )
            await session.execute(stmt)
            await session.commit()
        return user_answers

    def state_is_valid(self, state, event_id: int) -> bool:
        if not state:
            return False
        if not state.startswith(BotStates.dating):
            self.logger.answer_by_inline('error', f'Wrong state: {state}')
            return False
        dating_msg_id = int(state.split('_')[-2])
        if dating_msg_id != event_id:
            self.logger.answer_by_inline('error', f'Wrong dating_msg_id: {state}')
            return False
        return True

    async def reply_to_answer(
        self,
        client,
        event,
        question_idx,
        user_answers,
        dating_msg_id,
        tgbot,
        user
    ) -> None:
        dating_msg = await client.get_messages(
            event.chat_id, ids=dating_msg_id
        )
        if dating_msg:
            next_question_idx = question_idx + 1
            if next_question_idx > len(self.dating_questions):
                await self.state_machine.reset_state(tgbot, user)
                success_answer = (
                    f"{tgbot.dating_success_msg or 'Success'}\n"
                    f"{user_answers}"
                )
                await client.edit_message(
                    event.chat_id,
                    dating_msg_id,
                    success_answer,
                    buttons=get_dating_keyboard(tgbot)
                )
                await self.reset_user_answers(user)
                return
            new_question = self.dating_questions[next_question_idx]['question']
            new_answers = self.dating_questions[next_question_idx]['answers']
            await self.state_machine.set_state(
                f'{BotStates.dating}_{dating_msg_id}_{next_question_idx}',
                tgbot, user
            )
            if new_answers and new_answers[0]:
                buttons = get_answers_keyboard(new_answers)
            else:
                buttons = None
            print(f'{buttons=}')
            await client.edit_message(
                event.chat_id,
                dating_msg_id,
                new_question,
                buttons=buttons,
            )
        else:
            self.logger.answer_by_inline(
                'error', 'Message not found by id'
            )

    def wait_messages(self, client):
        state_checker = get_state_checker(self, BotStates.menu)

        @client.on(events.NewMessage(incoming=True, pattern='/start'))
        async def start_handler(event):
            # Регистрация пользователя
            tgbot = await self.get_tgbot_safely()
            await self.save_new_user(event, tgbot)
            # Приветствие
            await event.respond(
                tgbot.welcome_message or 'Start',
                # file=tgbot.welcome_photo if tgbot.welcome_photo else None,
                buttons=get_menu_keyboard(tgbot),
                link_preview=False
            )

        @client.on(events.CallbackQuery(pattern=b'lead_magnet_button'))
        async def lead_magnet_handler(event):
            tgbot = await self.get_tgbot_safely()
            user = await self.get_user(event.chat_id, tgbot)
            await self.state_machine.reset_state(tgbot, user)
            await event.respond(
                tgbot.lead_magnet_msg or 'Lead magnet',
                # file=tgbot.lead_magnet_photo if tgbot.welcome_photo else None,
                buttons=get_lead_magnet_keyboard(tgbot),
                link_preview=False
            )

        @client.on(events.CallbackQuery(pattern=b'dating_button'))
        async def dating_handler(event):
            tgbot = await self.get_tgbot_safely()
            if not self.dating_questions:
                await event.respond(
                    'Dating questions are not set',
                    buttons=get_dating_keyboard(tgbot)
                )
                return
            user = await self.get_user(event.chat_id, tgbot)
            await self.reset_user_answers(user)
            question_idx = 1
            first_question = self.dating_questions[question_idx]['question']
            answers = self.dating_questions[question_idx]['answers']
            if answers:
                buttons = get_answers_keyboard(answers)
            else:
                buttons = None
            dating_msg = await event.respond(
                first_question,
                buttons=buttons,
                link_preview=False
            )
            await self.state_machine.set_state(
                f'{BotStates.dating}_{dating_msg.id}_{question_idx}',
                tgbot, user
            )

        @client.on(events.CallbackQuery(pattern=b'answer_*'))
        async def answer_by_inline(event):
            tgbot = await self.get_tgbot_safely()
            user = await self.get_user(event.chat_id, tgbot)
            state = await self.state_machine.get_state(tgbot, user)
            if not self.state_is_valid(state):
                return await self.dating_handler(event)
            dating_msg_id, question_idx = [
                int(num) for num in state.split('_')
                if num.isdigit()
            ]
            answer_idx = int(event.data.decode("utf-8").split('_')[-1])
            user_answers = await self.save_user_button_answer(
                user, question_idx, answer_idx
            )

            await self.reply_to_answer(
                client, event, question_idx, user_answers, dating_msg_id,
                tgbot, user
            )

        @client.on(events.NewMessage(
            incoming=True,
            func=lambda e: e.date >= self.tgbot_data.started_at
            and e.is_private
        ))
        async def answer_hand_write(event):
            tgbot = await self.get_tgbot_safely()
            user = await self.get_user(event.chat_id, tgbot)
            state = await self.state_machine.get_state(tgbot, user)
            if not self.state_is_valid(state):
                return
            dating_msg_id, question_idx = [
                int(num) for num in state.split('_')
                if num.isdigit()
            ]
            user_answers = await self.save_user_hand_write_answer(
                user, question_idx, event.text
            )
            await self.reply_to_answer(
                client, event, question_idx, user_answers, dating_msg_id,
                tgbot, user
            )

        @client.on(events.CallbackQuery(pattern=b'info_button'))
        async def info_handler(event):
            tgbot = await self.get_tgbot_safely()
            user = await self.get_user(event.chat_id, tgbot)
            await self.state_machine.reset_state(tgbot, user)
            await event.respond(
                tgbot.info_msg or 'Info',
                buttons=get_info_keyboard(tgbot),
                link_preview=False
            )
