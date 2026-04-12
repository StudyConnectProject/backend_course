import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource
from app.repositories.resource_repository import ResourceRepository
from app.repositories.course_repository import CourseRepository
from app.schemas.resource import ResourceCreate, ResourceResponse


class ResourceService:
    def __init__(self, db: AsyncSession):
        self.repo = ResourceRepository(db)
        self.course_repo = CourseRepository(db)

    async def create_resource(
        self,
        course_id: uuid.UUID,
        data: ResourceCreate,
        uploaded_by: uuid.UUID,
        user_role: str,
    ) -> ResourceResponse:
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
        if user_role == "tutor" and course.tutor_id != uploaded_by:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "FORBIDDEN",
                    "message": "No tienes permisos para agregar recursos a este curso",
                    "status_code": 403,
                },
            )

        resource = Resource(
            course_id=course_id,
            title=data.title,
            type=data.type,
            url=data.url,
            description=data.description,
            uploaded_by=uploaded_by,
        )
        resource = await self.repo.create(resource)
        return ResourceResponse.model_validate(resource)

    async def list_resources(self, course_id: uuid.UUID) -> list[ResourceResponse]:
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
        resources = await self.repo.list_by_course(course_id)
        return [ResourceResponse.model_validate(r) for r in resources]

    async def delete_resource(
        self,
        course_id: uuid.UUID,
        resource_id: uuid.UUID,
        user_id: uuid.UUID,
        user_role: str,
    ) -> None:
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
        if user_role == "tutor" and course.tutor_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "FORBIDDEN",
                    "message": "No tienes permisos para eliminar recursos de este curso",
                    "status_code": 403,
                },
            )

        resource = await self.repo.get_by_id(resource_id)
        if not resource or resource.course_id != course_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "RESOURCE_NOT_FOUND",
                    "message": f"Recurso con id {resource_id} no encontrado",
                    "status_code": 404,
                },
            )
        await self.repo.delete(resource)
