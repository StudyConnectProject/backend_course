from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.models.enrollment import EnrollmentStatus


class EnrollmentResponse(BaseModel):
    id: UUID
    course_id: UUID
    student_id: UUID
    enrolled_at: datetime
    status: EnrollmentStatus

    model_config = {"from_attributes": True}


class StudentInCourse(BaseModel):
    student_id: UUID
    enrolled_at: datetime
    status: EnrollmentStatus

    model_config = {"from_attributes": True}


class TutorInfo(BaseModel):
    tutor_id: UUID
