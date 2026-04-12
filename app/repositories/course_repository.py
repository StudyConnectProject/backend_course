import uuid
import math
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course, CourseStatus
from app.models.enrollment import Enrollment, EnrollmentStatus


class CourseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, course: Course) -> Course:
        self.db.add(course)
        await self.db.flush()
        await self.db.refresh(course)
        return course

    async def get_by_id(self, course_id: uuid.UUID) -> Course | None:
        result = await self.db.execute(select(Course).where(Course.id == course_id))
        return result.scalar_one_or_none()

    async def list_courses(
        self,
        category: str | None = None,
        level: str | None = None,
        tutor_id: uuid.UUID | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Course], int]:
        query = select(Course)
        count_query = select(func.count()).select_from(Course)

        filters = []
        if category:
            filters.append(Course.category == category)
        if level:
            filters.append(Course.level == level)
        if tutor_id:
            filters.append(Course.tutor_id == tutor_id)
        if status:
            filters.append(Course.status == status)

        for f in filters:
            query = query.where(f)
            count_query = count_query.where(f)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Course.created_at.desc())
        result = await self.db.execute(query)
        courses = list(result.scalars().all())

        return courses, total

    async def search(
        self,
        q: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Course], int]:
        query = select(Course)
        count_query = select(func.count()).select_from(Course)

        filters = []
        if q:
            pattern = f"%{q}%"
            filters.append(
                or_(
                    Course.title.ilike(pattern),
                    Course.description.ilike(pattern),
                )
            )
        if category:
            filters.append(Course.category == category)

        for f in filters:
            query = query.where(f)
            count_query = count_query.where(f)

        # For tags filtering with JSON — handled at service level for SQLite compatibility in tests
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Course.created_at.desc())
        result = await self.db.execute(query)
        courses = list(result.scalars().all())

        # Filter by tags in Python if needed (SQLite doesn't support JSON operators)
        if tags:
            courses = [c for c in courses if any(t in (c.tags or []) for t in tags)]
            total = len(courses)

        return courses, total

    async def update(self, course: Course, data: dict) -> Course:
        for key, value in data.items():
            if value is not None:
                setattr(course, key, value)
        await self.db.flush()
        await self.db.refresh(course)
        return course

    async def soft_delete(self, course: Course) -> None:
        course.status = CourseStatus.inactive
        await self.db.flush()

    async def get_enrolled_count(self, course_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Enrollment)
            .where(
                Enrollment.course_id == course_id,
                Enrollment.status == EnrollmentStatus.active,
            )
        )
        return result.scalar() or 0
