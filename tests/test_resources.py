import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import (
    tutor_headers,
    student_headers,
    admin_headers,
    create_test_course,
    create_test_resource,
    TUTOR_ID,
)


@pytest.mark.asyncio
async def test_create_resource_as_tutor(client: AsyncClient, db_session):
    course = await create_test_course(db_session, tutor_id=TUTOR_ID)
    await db_session.commit()

    body = {
        "title": "Slide Deck",
        "type": "document",
        "url": "https://example.com/slides.pdf",
        "description": "Course slides",
    }
    resp = await client.post(
        f"/api/v1/courses/{course.id}/resources", json=body, headers=tutor_headers()
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Slide Deck"
    assert data["course_id"] == str(course.id)
    assert data["uploaded_by"] == str(TUTOR_ID)


@pytest.mark.asyncio
async def test_create_resource_forbidden_for_student(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await db_session.commit()

    body = {
        "title": "Hack",
        "type": "link",
        "url": "https://evil.com",
    }
    resp = await client.post(
        f"/api/v1/courses/{course.id}/resources", json=body, headers=student_headers()
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_resources(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await create_test_resource(db_session, course.id, title="Resource 1")
    await create_test_resource(db_session, course.id, title="Resource 2")
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/courses/{course.id}/resources", headers=tutor_headers()
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_delete_resource_success(client: AsyncClient, db_session):
    course = await create_test_course(db_session, tutor_id=TUTOR_ID)
    resource = await create_test_resource(db_session, course.id)
    await db_session.commit()

    resp = await client.delete(
        f"/api/v1/courses/{course.id}/resources/{resource.id}",
        headers=tutor_headers(),
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_resource_not_found(client: AsyncClient, db_session):
    course = await create_test_course(db_session, tutor_id=TUTOR_ID)
    await db_session.commit()
    fake_id = uuid.uuid4()

    resp = await client.delete(
        f"/api/v1/courses/{course.id}/resources/{fake_id}",
        headers=tutor_headers(),
    )
    assert resp.status_code == 404
