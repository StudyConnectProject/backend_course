import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource


class ResourceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, resource: Resource) -> Resource:
        self.db.add(resource)
        await self.db.flush()
        await self.db.refresh(resource)
        return resource

    async def get_by_id(self, resource_id: uuid.UUID) -> Resource | None:
        result = await self.db.execute(
            select(Resource).where(Resource.id == resource_id)
        )
        return result.scalar_one_or_none()

    async def list_by_course(self, course_id: uuid.UUID) -> list[Resource]:
        result = await self.db.execute(
            select(Resource)
            .where(Resource.course_id == course_id)
            .order_by(Resource.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete(self, resource: Resource) -> None:
        await self.db.delete(resource)
        await self.db.flush()

    async def count_by_course(self, course_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Resource)
            .where(Resource.course_id == course_id)
        )
        return result.scalar() or 0
