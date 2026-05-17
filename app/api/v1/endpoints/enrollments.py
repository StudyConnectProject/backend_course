from uuid import UUID
from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user, require_role
from app.schemas.enrollment import EnrollmentResponse, StudentInCourse, TutorInfo
from app.schemas.common import PaginatedResponse
from app.services.enrollment_service import EnrollmentService
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["enrollments"])


class AddStudentBody(BaseModel):
    student_id: UUID


@router.post(
    "/{course_id}/enroll",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_in_course(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["student"])),
):
    service = EnrollmentService(db)
    return await service.enroll_student(course_id, current_user.id)


@router.delete(
    "/{course_id}/enroll",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_enrollment(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["student", "admin"])),
):
    service = EnrollmentService(db)
    await service.cancel_enrollment(course_id, current_user.id)


@router.get(
    "/{course_id}/students",
    response_model=PaginatedResponse[StudentInCourse],
)
async def list_students(
    course_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["tutor", "admin"])),
):
    # Tutor can only see students of their own courses
    if current_user.role == "tutor":
        course_service = CourseService(db)
        course = await course_service.get_course_model(course_id)
        if course.tutor_id != current_user.id:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "FORBIDDEN",
                    "message": "No tienes permisos para ver los estudiantes de este curso",
                    "status_code": 403,
                },
            )
    service = EnrollmentService(db)
    return await service.list_students(course_id, page, page_size)


@router.get(
    "/{course_id}/tutor",
    response_model=TutorInfo,
)
async def get_course_tutor(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    service = EnrollmentService(db)
    return await service.get_tutor_info(course_id)


@router.post(
    "/{course_id}/students",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_student(
    course_id: UUID,
    body: AddStudentBody,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["tutor", "admin"])),
):
    if current_user.role == "tutor":
        course_service = CourseService(db)
        course = await course_service.get_course_model(course_id)
        if course.tutor_id != current_user.id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail={"error": "FORBIDDEN", "message": "No puedes modificar este curso", "status_code": 403})
    service = EnrollmentService(db)
    return await service.add_student_by_tutor(course_id, body.student_id)


@router.delete(
    "/{course_id}/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_student(
    course_id: UUID,
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["tutor", "admin"])),
):
    if current_user.role == "tutor":
        course_service = CourseService(db)
        course = await course_service.get_course_model(course_id)
        if course.tutor_id != current_user.id:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail={"error": "FORBIDDEN", "message": "No puedes modificar este curso", "status_code": 403})
    service = EnrollmentService(db)
    await service.remove_student_by_tutor(course_id, student_id)
