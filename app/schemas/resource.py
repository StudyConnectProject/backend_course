from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.models.resource import ResourceType


class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    type: ResourceType
    url: str = Field(..., min_length=1, max_length=1000)
    description: str | None = None


class ResourceResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    type: ResourceType
    url: str
    description: str | None = None
    uploaded_by: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
