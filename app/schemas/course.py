from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.course import CourseLevel, CourseStatus


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)
    level: CourseLevel
    tutor_id: UUID
    tags: list[str] = Field(default_factory=list)


class CourseUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, min_length=1, max_length=100)
    level: CourseLevel | None = None
    tags: list[str] | None = None
    thumbnail_url: str | None = None


class CourseSummary(BaseModel):
    id: UUID
    title: str
    category: str
    level: CourseLevel
    status: CourseStatus
    tutor_id: UUID
    enrolled_count: int = 0

    model_config = {"from_attributes": True}


class CourseResponse(BaseModel):
    id: UUID
    title: str
    description: str
    category: str
    level: CourseLevel
    status: CourseStatus
    tutor_id: UUID
    thumbnail_url: str | None = None
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CourseDetailResponse(CourseResponse):
    enrolled_count: int = 0
    resource_count: int = 0


class StatusUpdate(BaseModel):
    status: CourseStatus


class SearchParams(BaseModel):
    q: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
