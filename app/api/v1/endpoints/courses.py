from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user, require_role
from app.schemas.course import (
    CourseCreate,
    CourseUpdate,
    CourseResponse,
    CourseDetailResponse,
    CourseSummary,
    StatusUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.course_service import CourseService
from app.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_course(
    body: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["tutor", "admin"])),
):
    service = CourseService(db)
    return await service.create_course(body)


@router.get(
    "/search",
    response_model=PaginatedResponse[CourseSummary],
)
async def search_courses(
    q: str | None = None,
    category: str | None = None,
    tags: list[str] = Query(default=[]),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    service = CourseService(db)
    return await service.search_courses(
        q=q, category=category, tags=tags or None, page=page, page_size=page_size
    )


@router.get(
    "/my-enrollments",
    response_model=list[UUID],
    tags=["enrollments"],
)
async def my_enrollments(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["student"])),
):
    service = EnrollmentService(db)
    return await service.list_my_enrollments(current_user.id)


@router.get(
    "",
    response_model=PaginatedResponse[CourseSummary],
)
async def list_courses(
    category: str | None = None,
    level: str | None = None,
    tutor_id: UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    service = CourseService(db)
    return await service.list_courses(
        category=category,
        level=level,
        tutor_id=tutor_id,
        course_status=status_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{course_id}",
    response_model=CourseDetailResponse,
)
async def get_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    service = CourseService(db)
    return await service.get_course(course_id)


@router.put(
    "/{course_id}",
    response_model=CourseResponse,
)
async def update_course(
    course_id: UUID,
    body: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["tutor", "admin"])),
):
    service = CourseService(db)
    return await service.update_course(course_id, body, current_user.id, current_user.role)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["tutor", "admin"])),
):
    service = CourseService(db)
    await service.delete_course(course_id, current_user.id, current_user.role)


@router.patch(
    "/{course_id}/status",
    response_model=CourseResponse,
)
async def update_course_status(
    course_id: UUID,
    body: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["tutor", "admin"])),
):
    service = CourseService(db)
    return await service.update_status(course_id, body, current_user.id, current_user.role)
