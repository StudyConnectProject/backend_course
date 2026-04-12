import uuid
import asyncio
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from jose import jwt

from app.models.course import Base, Course, CourseLevel, CourseStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.resource import Resource, ResourceType
from app.core.database import get_db
from app.dependencies.auth import get_current_user, CurrentUser
from app.main import app

DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

SECRET_KEY = "shared-secret-key-from-auth-service-min-32-chars"
ALGORITHM = "HS256"

TUTOR_ID = uuid.uuid4()
STUDENT_ID = uuid.uuid4()
ADMIN_ID = uuid.uuid4()
OTHER_TUTOR_ID = uuid.uuid4()


def make_token(user_id: uuid.UUID, role: str) -> str:
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


TUTOR_TOKEN = make_token(TUTOR_ID, "tutor")
STUDENT_TOKEN = make_token(STUDENT_ID, "student")
ADMIN_TOKEN = make_token(ADMIN_ID, "admin")
OTHER_TUTOR_TOKEN = make_token(OTHER_TUTOR_ID, "tutor")


def tutor_headers():
    return {"Authorization": f"Bearer {TUTOR_TOKEN}"}


def student_headers():
    return {"Authorization": f"Bearer {STUDENT_TOKEN}"}


def admin_headers():
    return {"Authorization": f"Bearer {ADMIN_TOKEN}"}


def other_tutor_headers():
    return {"Authorization": f"Bearer {OTHER_TUTOR_TOKEN}"}


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def create_test_course(
    db: AsyncSession,
    tutor_id: uuid.UUID = TUTOR_ID,
    title: str = "Test Course",
    category: str = "programming",
    level: CourseLevel = CourseLevel.beginner,
    status: CourseStatus = CourseStatus.active,
    tags: list[str] | None = None,
) -> Course:
    course = Course(
        title=title,
        description="A test course description",
        category=category,
        level=level,
        status=status,
        tutor_id=tutor_id,
        tags=tags or ["python", "testing"],
    )
    db.add(course)
    await db.flush()
    await db.refresh(course)
    return course


async def create_test_enrollment(
    db: AsyncSession,
    course_id: uuid.UUID,
    student_id: uuid.UUID = STUDENT_ID,
    status: EnrollmentStatus = EnrollmentStatus.active,
) -> Enrollment:
    enrollment = Enrollment(
        course_id=course_id,
        student_id=student_id,
        status=status,
    )
    db.add(enrollment)
    await db.flush()
    await db.refresh(enrollment)
    return enrollment


async def create_test_resource(
    db: AsyncSession,
    course_id: uuid.UUID,
    uploaded_by: uuid.UUID = TUTOR_ID,
    title: str = "Test Resource",
    resource_type: ResourceType = ResourceType.link,
) -> Resource:
    resource = Resource(
        course_id=course_id,
        title=title,
        type=resource_type,
        url="https://example.com/resource",
        description="A test resource",
        uploaded_by=uploaded_by,
    )
    db.add(resource)
    await db.flush()
    await db.refresh(resource)
    return resource
