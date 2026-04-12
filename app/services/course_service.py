import uuid
import math

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course, CourseStatus
from app.repositories.course_repository import CourseRepository
from app.repositories.resource_repository import ResourceRepository
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseDetailResponse,
    CourseSummary,
    StatusUpdate,
)
from app.schemas.common import PaginatedResponse


class CourseService:
    def __init__(self, db: AsyncSession):
        self.repo = CourseRepository(db)
        self.resource_repo = ResourceRepository(db)

    async def create_course(self, data: CourseCreate) -> CourseResponse:
        course = Course(
            title=data.title,
            description=data.description,
            category=data.category,
            level=data.level,
            tutor_id=data.tutor_id,
            tags=data.tags,
        )
        course = await self.repo.create(course)
        return CourseResponse.model_validate(course)

    async def get_course(self, course_id: uuid.UUID) -> CourseDetailResponse:
        course = await self.repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "COURSE_NOT_FOUND",
                    "message": f"Curso con id {course_id} no encontrado",
                    "status_code": 404,
                },
            )
        enrolled_count = await self.repo.get_enrolled_count(course_id)
        resource_count = await self.resource_repo.count_by_course(course_id)
        data = CourseDetailResponse.model_validate(course)
        data.enrolled_count = enrolled_count
        data.resource_count = resource_count
        return data

    async def list_courses(
        self,
        category: str | None = None,
        level: str | None = None,
        tutor_id: uuid.UUID | None = None,
        course_status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[CourseSummary]:
        courses, total = await self.repo.list_courses(
            category=category,
            level=level,
            tutor_id=tutor_id,
            status=course_status,
            page=page,
            page_size=page_size,
        )
        items = []
        for c in courses:
            enrolled_count = await self.repo.get_enrolled_count(c.id)
            summary = CourseSummary.model_validate(c)
            summary.enrolled_count = enrolled_count
            items.append(summary)

        pages = math.ceil(total / page_size) if total > 0 else 0
        return PaginatedResponse[CourseSummary](
            items=items, total=total, page=page, page_size=page_size, pages=pages
        )

    async def search_courses(
        self,
        q: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[CourseSummary]:
        courses, total = await self.repo.search(
            q=q, category=category, tags=tags, page=page, page_size=page_size
        )
        items = []
        for c in courses:
            enrolled_count = await self.repo.get_enrolled_count(c.id)
            summary = CourseSummary.model_validate(c)
            summary.enrolled_count = enrolled_count
            items.append(summary)

        pages = math.ceil(total / page_size) if total > 0 else 0
        return PaginatedResponse[CourseSummary](
            items=items, total=total, page=page, page_size=page_size, pages=pages
        )

    async def update_course(
        self, course_id: uuid.UUID, data: CourseUpdate, user_id: uuid.UUID, user_role: str
    ) -> CourseResponse:
        course = await self.repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "COURSE_NOT_FOUND",
                    "message": f"Curso con id {course_id} no encontrado",
                    "status_code": 404,
                },
            )
        if user_role == "tutor" and course.tutor_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "FORBIDDEN",
                    "message": "No tienes permisos para actualizar este curso",
                    "status_code": 403,
                },
            )
        update_data = data.model_dump(exclude_unset=True)
        course = await self.repo.update(course, update_data)
        return CourseResponse.model_validate(course)

    async def delete_course(
        self, course_id: uuid.UUID, user_id: uuid.UUID, user_role: str
    ) -> None:
        course = await self.repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "COURSE_NOT_FOUND",
                    "message": f"Curso con id {course_id} no encontrado",
                    "status_code": 404,
                },
            )
        if user_role == "tutor" and course.tutor_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "FORBIDDEN",
                    "message": "No tienes permisos para eliminar este curso",
                    "status_code": 403,
                },
            )
        await self.repo.soft_delete(course)

    async def update_status(
        self, course_id: uuid.UUID, data: StatusUpdate, user_id: uuid.UUID, user_role: str
    ) -> CourseResponse:
        course = await self.repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "COURSE_NOT_FOUND",
                    "message": f"Curso con id {course_id} no encontrado",
                    "status_code": 404,
                },
            )
        if user_role == "tutor" and course.tutor_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "FORBIDDEN",
                    "message": "No tienes permisos para cambiar el estado de este curso",
                    "status_code": 403,
                },
            )
        course = await self.repo.update(course, {"status": data.status})
        return CourseResponse.model_validate(course)

    async def get_course_model(self, course_id: uuid.UUID) -> Course:
        """Get raw Course model — used by other services to check ownership."""
        course = await self.repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "COURSE_NOT_FOUND",
                    "message": f"Curso con id {course_id} no encontrado",
                    "status_code": 404,
                },
            )
        return course
