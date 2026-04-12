from fastapi import APIRouter

from app.api.v1.endpoints import courses, enrollments, resources

router = APIRouter(prefix="/api/v1")

# Register courses first — search endpoint must be before {id} routes
router.include_router(courses.router)
router.include_router(enrollments.router)
router.include_router(resources.router)
