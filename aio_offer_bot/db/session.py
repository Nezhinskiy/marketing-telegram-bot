import asyncio
from typing import Sequence

from sqlalchemy import NullPool, and_, create_engine, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import Session, selectinload, sessionmaker
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)

import config
from core.utils import log_stack_for_retry
from db.base import Base
from db.utils import get_postgres_dsn

default_engine = create_async_engine(
    get_postgres_dsn(), poolclass=NullPool,
    connect_args={'timeout': config.ASYNCPG_TIMEOUT}
)
sync_engine = create_engine(
    get_postgres_dsn(is_async=False), poolclass=NullPool
)


class QueryAsyncSession(AsyncSession):
    """
    Добавим в сессию самые часто используемые операции типа запросов с
    условием.
    """
    @retry(retry=retry_if_exception_type(asyncio.TimeoutError),
           stop=stop_after_attempt(config.MAX_RETRIES_DB_REQUESTS),
           wait=wait_fixed(config.RETRY_DELAY_DB_REQUESTS),
           reraise=True,
           before_sleep=log_stack_for_retry)
    async def execute(self, *args, **kwargs):
        return await super().execute(*args, **kwargs)

    def _get_conditions(self, model, filters):
        return [
            getattr(model, key) == value
            for key, value in filters.items()
        ]

    async def filter_by(
        self,
        model: Base,
        filters: dict,
        load_related: list | None = None
    ) -> Sequence:
        stmt = select(model)
        if load_related:
            stmt = stmt.options(*[selectinload(rel) for rel in load_related])
        stmt = stmt.where(and_(*self._get_conditions(model, filters)))
        cursor = await self.execute(stmt)
        return cursor.scalars().all()

    async def first(
        self,
        model: Base,
        filters: dict,
        load_related: list | None = None
    ) -> Base:
        stmt = select(model)
        if load_related:
            stmt = stmt.options(*[selectinload(rel) for rel in load_related])
        stmt = stmt.where(and_(*self._get_conditions(model, filters)))
        cursor = await self.execute(stmt)
        return cursor.scalar()

    async def update(self, model: Base, filters: dict, update_data: dict):
        conditions = self._get_conditions(model, filters)
        stmt = update(model).values(update_data).where(and_(*conditions))
        await self.execute(stmt)
        await self.commit()


AsyncSessionType = async_sessionmaker[QueryAsyncSession]
SyncSessionType = sessionmaker[Session]


def get_session(engine=None) -> AsyncSessionType:
    engine = engine or default_engine
    return async_sessionmaker(
        engine, class_=QueryAsyncSession, expire_on_commit=False)


def get_sync_session(engine=None) -> SyncSessionType:
    engine = engine or sync_engine
    return sessionmaker(engine, expire_on_commit=False)
