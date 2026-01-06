"""
Base Repository - Generic async repository pattern for BDOCS.

Provides common CRUD operations for all entities using SQLAlchemy async.
"""
from typing import TypeVar, Generic, Optional, List, Type
from uuid import UUID

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.async_db import AsyncBase

# Generic type for model classes
T = TypeVar('T', bound=AsyncBase)


class AsyncBaseRepository(Generic[T]):
    """
    Generic async repository providing common database operations.

    Usage:
        class InmateRepository(AsyncBaseRepository[Inmate]):
            def __init__(self, session: AsyncSession):
                super().__init__(Inmate, session)
    """

    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get a single record by UUID primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[T]:
        """Get all records with pagination."""
        query = select(self.model)

        # Exclude soft-deleted records by default
        if hasattr(self.model, 'is_deleted') and not include_deleted:
            query = query.where(self.model.is_deleted == False)  # noqa: E712

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, include_deleted: bool = False) -> int:
        """Get total count of records."""
        query = select(func.count()).select_from(self.model)

        if hasattr(self.model, 'is_deleted') and not include_deleted:
            query = query.where(self.model.is_deleted == False)  # noqa: E712

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create(self, entity: T) -> T:
        """Create a new record."""
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        """Update an existing record."""
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: UUID, soft: bool = True) -> bool:
        """
        Delete a record.

        Args:
            id: UUID of the record to delete
            soft: If True, sets is_deleted=True; if False, permanently deletes

        Returns:
            True if record was found and deleted, False otherwise
        """
        entity = await self.get_by_id(id)
        if not entity:
            return False

        if soft and hasattr(entity, 'is_deleted'):
            entity.is_deleted = True
            await self.session.flush()
        else:
            await self.session.delete(entity)
            await self.session.flush()

        return True

    async def exists(self, id: UUID) -> bool:
        """Check if a record exists by ID."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0
