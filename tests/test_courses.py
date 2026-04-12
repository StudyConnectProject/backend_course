import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.conftest import (
    tutor_headers,
    student_headers,
    admin_headers,
    other_tutor_headers,
    create_test_course,
    TUTOR_ID,
    OTHER_TUTOR_ID,
)


@pytest.mark.asyncio
async def test_create_course_as_tutor(client: AsyncClient):
    body = {
        "title": "FastAPI Course",
        "description": "Learn FastAPI from scratch",
        "category": "programming",
        "level": "beginner",
        "tutor_id": str(TUTOR_ID),
        "tags": ["python", "fastapi"],
    }
    resp = await client.post("/api/v1/courses", json=body, headers=tutor_headers())
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "FastAPI Course"
    assert data["category"] == "programming"
    assert data["level"] == "beginner"
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_create_course_forbidden_for_student(client: AsyncClient):
    body = {
        "title": "Forbidden Course",
        "description": "Should fail",
        "category": "test",
        "level": "beginner",
        "tutor_id": str(uuid.uuid4()),
        "tags": [],
    }
    resp = await client.post("/api/v1/courses", json=body, headers=student_headers())
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_course_validation_error(client: AsyncClient):
    body = {
        "description": "Missing title",
        "category": "test",
        "level": "beginner",
        "tutor_id": str(uuid.uuid4()),
    }
    resp = await client.post("/api/v1/courses", json=body, headers=tutor_headers())
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_course_by_id(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await db_session.commit()

    resp = await client.get(f"/api/v1/courses/{course.id}", headers=tutor_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(course.id)
    assert data["title"] == "Test Course"
    assert "enrolled_count" in data
    assert "resource_count" in data


@pytest.mark.asyncio
async def test_get_course_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/courses/{fake_id}", headers=tutor_headers())
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_courses_paginated(client: AsyncClient, db_session):
    for i in range(5):
        await create_test_course(db_session, title=f"Course {i}")
    await db_session.commit()

    resp = await client.get(
        "/api/v1/courses", params={"page": 1, "page_size": 2}, headers=tutor_headers()
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["pages"] == 3


@pytest.mark.asyncio
async def test_list_courses_with_category_filter(client: AsyncClient, db_session):
    await create_test_course(db_session, title="Python Course", category="programming")
    await create_test_course(db_session, title="History Course", category="humanities")
    await db_session.commit()

    resp = await client.get(
        "/api/v1/courses", params={"category": "programming"}, headers=tutor_headers()
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["category"] == "programming"


@pytest.mark.asyncio
async def test_update_course_as_owner(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await db_session.commit()

    resp = await client.put(
        f"/api/v1/courses/{course.id}",
        json={"title": "Updated Title"},
        headers=tutor_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_course_forbidden_other_tutor(client: AsyncClient, db_session):
    course = await create_test_course(db_session, tutor_id=TUTOR_ID)
    await db_session.commit()

    resp = await client.put(
        f"/api/v1/courses/{course.id}",
        json={"title": "Hacked!"},
        headers=other_tutor_headers(),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_course_soft_delete(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await db_session.commit()

    resp = await client.delete(f"/api/v1/courses/{course.id}", headers=tutor_headers())
    assert resp.status_code == 204

    # Verify it's now inactive
    resp2 = await client.get(f"/api/v1/courses/{course.id}", headers=tutor_headers())
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "inactive"


@pytest.mark.asyncio
async def test_search_courses_by_text(client: AsyncClient, db_session):
    await create_test_course(db_session, title="Advanced Python")
    await create_test_course(db_session, title="Basic Math")
    await db_session.commit()

    resp = await client.get(
        "/api/v1/courses/search", params={"q": "python"}, headers=tutor_headers()
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert "Python" in data["items"][0]["title"]


@pytest.mark.asyncio
async def test_search_courses_by_category(client: AsyncClient, db_session):
    await create_test_course(db_session, title="Course A", category="science")
    await create_test_course(db_session, title="Course B", category="art")
    await db_session.commit()

    resp = await client.get(
        "/api/v1/courses/search", params={"category": "science"}, headers=tutor_headers()
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_search_courses_by_tags(client: AsyncClient, db_session):
    await create_test_course(db_session, title="Tagged Course", tags=["fastapi", "web"])
    await create_test_course(db_session, title="Other Course", tags=["math"])
    await db_session.commit()

    resp = await client.get(
        "/api/v1/courses/search", params={"tags": ["fastapi"]}, headers=tutor_headers()
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any("Tagged" in item["title"] for item in items)


@pytest.mark.asyncio
async def test_update_course_status(client: AsyncClient, db_session):
    course = await create_test_course(db_session)
    await db_session.commit()

    resp = await client.patch(
        f"/api/v1/courses/{course.id}/status",
        json={"status": "finished"},
        headers=tutor_headers(),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "finished"
