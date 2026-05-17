import uuid
import math

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.course import CourseStatus
from app.repositories.enrollment_repository import EnrollmentRepository
from app.repositories.course_repository import CourseRepository
from app.schemas.enrollment import EnrollmentResponse, StudentInCourse, TutorInfo
from app.schemas.common import PaginatedResponse


class EnrollmentService:
    def __init__(self, db: AsyncSession):
        self.repo = EnrollmentRepository(db)
        self.course_repo = CourseRepository(db)

    async def enroll_student(
        self, course_id: uuid.UUID, student_id: uuid.UUID
    ) -> EnrollmentResponse:
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "COURSE_NOT_FOUND",
                    "message": f"Curso con id {course_id} no encontrado",
                    "status_code": 404,
                },
            )
        if course.status != CourseStatus.active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "COURSE_NOT_ACTIVE",
                    "message": "No es posible inscribirse en un curso que no está activo",
                    "status_code": 400,
                },
            )

        existing = await self.repo.get_by_course_and_student(course_id, student_id)
        if existing:
            if existing.status == EnrollmentStatus.active:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "ALREADY_ENROLLED",
                        "message": "Ya estás inscrito en este curso",
                        "status_code": 409,
                    },
                )
            # Reactivate cancelled enrollment instead of inserting a new row
            existing.status = EnrollmentStatus.active
            await self.repo.db.flush()
            await self.repo.db.refresh(existing)
            return EnrollmentResponse.model_validate(existing)

        enrollment = Enrollment(
            course_id=course_id,
            student_id=student_id,
        )
        enrollment = await self.repo.create(enrollment)
        return EnrollmentResponse.model_validate(enrollment)

    async def cancel_enrollment(
        self, course_id: uuid.UUID, student_id: uuid.UUID
    ) -> None:
        enrollment = await self.repo.get_active_by_course_and_student(course_id, student_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "ENROLLMENT_NOT_FOUND",
                    "message": "No se encontró una inscripción activa",
                    "status_code": 404,
                },
            )
        await self.repo.cancel(enrollment)

    async def list_students(
        self,
        course_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[StudentInCourse]:
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "COURSE_NOT_FOUND",
                    "message": f"Curso con id {course_id} no encontrado",
                    "status_code": 404,
                },
            )

        enrollments, total = await self.repo.list_by_course(course_id, page, page_size)
        items = [StudentInCourse.model_validate(e) for e in enrollments]
        pages = math.ceil(total / page_size) if total > 0 else 0
        return PaginatedResponse[StudentInCourse](
            items=items, total=total, page=page, page_size=page_size, pages=pages
        )

    async def get_tutor_info(self, course_id: uuid.UUID) -> TutorInfo:
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "COURSE_NOT_FOUND",
                    "message": f"Curso con id {course_id} no encontrado",
                    "status_code": 404,
                },
            )
        return TutorInfo(tutor_id=course.tutor_id)

    async def list_my_enrollments(self, student_id: uuid.UUID) -> list[uuid.UUID]:
        enrollments = await self.repo.list_by_student(student_id)
        return [e.course_id for e in enrollments]

    async def add_student_by_tutor(
        self, course_id: uuid.UUID, student_id: uuid.UUID
    ) -> EnrollmentResponse:
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "COURSE_NOT_FOUND", "message": f"Curso {course_id} no encontrado", "status_code": 404},
            )
        existing = await self.repo.get_active_by_course_and_student(course_id, student_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "ALREADY_ENROLLED", "message": "El estudiante ya está inscrito", "status_code": 409},
            )
        enrollment = Enrollment(course_id=course_id, student_id=student_id)
        enrollment = await self.repo.create(enrollment)
        return EnrollmentResponse.model_validate(enrollment)

    async def remove_student_by_tutor(
        self, course_id: uuid.UUID, student_id: uuid.UUID
    ) -> None:
        enrollment = await self.repo.get_active_by_course_and_student(course_id, student_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "ENROLLMENT_NOT_FOUND", "message": "No se encontró una inscripción activa", "status_code": 404},
            )
        await self.repo.cancel(enrollment)
