import asyncio
import traceback
from dataclasses import make_dataclass
from typing import Any, List, Tuple

from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from tg_logger import BaseLogger

from db.base import Base
from db.models import DatingQuestion, TGBot
from db.models.bot_user import BotUser
from db.session import AsyncSessionType, get_session

logger = BaseLogger()

async def execute_db_query(async_session, stmt):
    async with async_session() as session:
        cursor = False
        while not cursor:
            try:
                cursor = await session.execute(stmt)
            except (ConnectionRefusedError, ConnectionError):
                logger.error('Проснись, база отвалилась')
                await asyncio.sleep(5)
        return cursor.scalars().all()


async def get_admin_list(async_session):
    admin_stmt = select(BotUser.tg_id).where(BotUser.admin.is_(True))
    return await execute_db_query(async_session, admin_stmt)


async def get_tgbots(async_session, **filters):
    conditions = []

    for key, value in filters.items():
        key_parts = key.split('__')
        field_name = key_parts[0]

        if len(key_parts) > 1 and key_parts[1] == 'in':
            if value:  # Если список пуст, условие не будет учитываться
                conditions.append(getattr(TGBot, field_name).in_(value))
        else:
            conditions.append(getattr(TGBot, field_name) == value)
    stmt = (
        select(TGBot).where(and_(*conditions))
    )
    return await execute_db_query(async_session, stmt)


async def get_entities(**filters):
    async_session = get_session()
    tgbot_list = await get_tgbots(async_session, **filters)
    admin_list = await get_admin_list(async_session)
    return tgbot_list, admin_list


def get_tgbots_and_admins(**filters) -> Tuple[List[int], List[int]]:
    loop = asyncio.new_event_loop()
    tgbot_list, admin_list = loop.run_until_complete(
        get_entities(**filters))
    loop.close()
    return tgbot_list, admin_list


def create_dataclass_from_sqlalchemy_obj(db_obj: Base) -> Any:
    """
    Создаёт DataClass из экземпляра модели SQLAlchemy.
    И сохраняет в него данные всех полей.
    """
    cls = make_dataclass(
        f'DataClass{db_obj.__class__.__name__}',
        [
            (field, type(getattr(db_obj, field)))
            for field in db_obj.__table__.columns.keys()
        ]
    )
    return cls(**{
        field: getattr(db_obj, field)
        for field in db_obj.__table__.columns.keys()
    })


async def get_object_safely(
        obj: Base,
        model: Base,
        filter_dict: dict[str, Any],
        async_session: AsyncSessionType,
        logger: BaseLogger,
) -> Base:
    try:
        for table_name in filter_dict.keys():
            getattr(model, table_name)
            break
    except SQLAlchemyError as exc:
        logger.safe_get_object(
            'error',
            f'Error with safe_get_object model={model.__name__}: {exc}\n'
            f'Traceback: {traceback.format_exc()}'
        )
        async with async_session() as session:
            obj = await session.first(model, filter_dict)
    return obj


async def get_tgbot_dating_questions(
    async_session: AsyncSessionType, tgbot: TGBot
) -> list[DatingQuestion]:
    async with async_session() as session:
        stmt = (
            select(DatingQuestion)
            .where(DatingQuestion.tgbot == tgbot)
            .order_by(DatingQuestion.position, DatingQuestion.id)
        )
        cursor = await session.execute(stmt)
        return cursor.scalars().all()


async def get_dating_questions_dict(
    async_session: AsyncSessionType,
    tgbot: TGBot
) -> dict[int, Any]:
    questions = await get_tgbot_dating_questions(async_session, tgbot)
    questions_dict = {}
    for i, question in enumerate(questions):
        dataclass_question = create_dataclass_from_sqlalchemy_obj(question)
        questions_dict[i] = {
            'question': dataclass_question.question,
            'answers': dataclass_question.answers
        }
    logger.info(f'{questions_dict=}')
    return questions_dict
