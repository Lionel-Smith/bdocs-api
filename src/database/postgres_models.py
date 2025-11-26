from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from src.database.async_db import AsyncBase


class AsyncBaseModel(AsyncAttrs, AsyncBase):
    """Base model for PostgreSQL with async support and audit fields"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    inserted_date = Column(DateTime, server_default=func.now(), nullable=False)
    updated_date = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
