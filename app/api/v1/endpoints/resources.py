from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth import CurrentUser, get_current_user, require_role
from app.schemas.resource import ResourceCreate, ResourceResponse
from app.services.resource_service import ResourceService

router = APIRouter(prefix="/courses", tags=["resources"])


@router.post(
    "/{course_id}/resources",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_resource(
    course_id: UUID,
    body: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["tutor", "admin"])),
):
    service = ResourceService(db)
    return await service.create_resource(
        course_id, body, current_user.id, current_user.role
    )


@router.get(
    "/{course_id}/resources",
    response_model=list[ResourceResponse],
)
async def list_resources(
    course_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    service = ResourceService(db)
    return await service.list_resources(course_id)


@router.delete(
    "/{course_id}/resources/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_resource(
    course_id: UUID,
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_role(["tutor", "admin"])),
):
    service = ResourceService(db)
    await service.delete_resource(course_id, resource_id, current_user.id, current_user.role)
