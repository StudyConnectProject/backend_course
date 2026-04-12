import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment, EnrollmentStatus


class EnrollmentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, enrollment: Enrollment) -> Enrollment:
        self.db.add(enrollment)
        await self.db.flush()
        await self.db.refresh(enrollment)
        return enrollment

    async def get_by_course_and_student(
        self, course_id: uuid.UUID, student_id: uuid.UUID
    ) -> Enrollment | None:
        result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.course_id == course_id,
                Enrollment.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_course_and_student(
        self, course_id: uuid.UUID, student_id: uuid.UUID
    ) -> Enrollment | None:
        result = await self.db.execute(
            select(Enrollment).where(
                Enrollment.course_id == course_id,
                Enrollment.student_id == student_id,
                Enrollment.status == EnrollmentStatus.active,
            )
        )
        return result.scalar_one_or_none()

    async def cancel(self, enrollment: Enrollment) -> None:
        enrollment.status = EnrollmentStatus.cancelled
        await self.db.flush()

    async def list_by_course(
        self,
        course_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Enrollment], int]:
        count_query = (
            select(func.count())
            .select_from(Enrollment)
            .where(
                Enrollment.course_id == course_id,
                Enrollment.status == EnrollmentStatus.active,
            )
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        offset = (page - 1) * page_size
        query = (
            select(Enrollment)
            .where(
                Enrollment.course_id == course_id,
                Enrollment.status == EnrollmentStatus.active,
            )
            .offset(offset)
            .limit(page_size)
            .order_by(Enrollment.enrolled_at.desc())
        )
        result = await self.db.execute(query)
        enrollments = list(result.scalars().all())

        return enrollments, total
