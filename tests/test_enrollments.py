import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.models.course import CourseStatus, CourseLevel
from tests.conftest import (
    tutor_headers,
    student_headers,
    admin_headers,
    other_tutor_headers,
    create_test_course,
    create_test_enrollment,
    TUTOR_ID,
    STUDENT_ID,
)


@pytest.mark.asyncio
async def test_enroll_student_success(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/courses/{course.id}/enroll", headers=student_headers()
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["course_id"] == str(course.id)
    assert data["student_id"] == str(STUDENT_ID)
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_enroll_already_enrolled(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await create_test_enrollment(db_session, course.id, STUDENT_ID)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/courses/{course.id}/enroll", headers=student_headers()
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_enroll_inactive_course(client: AsyncClient, db_session):
    course = await create_test_course(db_session, status=CourseStatus.inactive)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/courses/{course.id}/enroll", headers=student_headers()
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_cancel_enrollment_success(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await create_test_enrollment(db_session, course.id, STUDENT_ID)
    await db_session.commit()

    resp = await client.delete(
        f"/api/v1/courses/{course.id}/enroll", headers=student_headers()
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_cancel_enrollment_not_found(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await db_session.commit()

    resp = await client.delete(
        f"/api/v1/courses/{course.id}/enroll", headers=student_headers()
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_students_as_tutor(client: AsyncClient, db_session):
    course = await create_test_course(db_session, tutor_id=TUTOR_ID)
    await create_test_enrollment(db_session, course.id, STUDENT_ID)
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/courses/{course.id}/students", headers=tutor_headers()
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["student_id"] == str(STUDENT_ID)


@pytest.mark.asyncio
async def test_list_students_forbidden_for_student(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/courses/{course.id}/students", headers=student_headers()
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_tutor_info(client: AsyncClient, db_session):
    course = await create_test_course(db_session, tutor_id=TUTOR_ID)
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/courses/{course.id}/tutor", headers=student_headers()
    )
    assert resp.status_code == 200
    assert resp.json()["tutor_id"] == str(TUTOR_ID)
