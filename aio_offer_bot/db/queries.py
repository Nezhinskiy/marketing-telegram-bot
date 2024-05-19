from operator import and_

from sqlalchemy import exists, func, select

from db.base import Base


def get_exists(model: Base, filters: dict):
    """Вернуть exists SqlAlchemy statement из словаря."""
    conditions = [
        getattr(model, key) == value
        for key, value in filters.items()
    ]
    filter_condition = and_(*conditions)
    return exists(model).where(filter_condition).select()


def get_count(model: Base):
    return select(func.count()).select_from(model)
