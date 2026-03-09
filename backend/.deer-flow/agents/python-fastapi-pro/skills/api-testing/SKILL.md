---
name: api-testing
description: Testing patterns for FastAPI applications using pytest, httpx, and TestClient. Use when writing integration tests, mocking dependencies, or testing async endpoints.
---

# API Testing for FastAPI

Write comprehensive tests for FastAPI applications with async support and proper dependency mocking.

## When to Use This Skill

- Writing integration tests for FastAPI endpoints
- Mocking dependencies (database, external services)
- Testing async endpoints and background tasks
- Setting up test databases and fixtures
- Testing authentication and authorization

## Core Patterns

### Pattern 1: Test Setup with TestClient

Basic FastAPI testing setup.

```python
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from main import app

# Sync tests
@pytest.fixture
def client():
    return TestClient(app)

# Async tests (preferred for async endpoints)
@pytest.fixture
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
```

### Pattern 2: Dependency Override

Mock dependencies for isolated tests.

```python
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

async def mock_get_db():
    # Use test database or in-memory SQLite
    async with TestAsyncSessionLocal() as session:
        yield session

@pytest.fixture(autouse=True)
def override_dependencies(app: FastAPI):
    app.dependency_overrides[get_db] = mock_get_db
    yield
    app.dependency_overrides.clear()

# Usage
async def test_get_user(async_client: AsyncClient):
    response = await async_client.get("/users/1")
    assert response.status_code == 200
```

### Pattern 3: Database Fixtures

Set up test database with proper cleanup.

```python
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test_db"

test_engine = create_async_engine(TEST_DATABASE_URL)

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def app_with_overrides(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield app
    app.dependency_overrides.clear()
```

### Pattern 4: Testing Async Endpoints

Proper async test patterns.

```python
import pytest

@pytest.mark.asyncio
async def test_create_user(async_client: AsyncClient):
    response = await async_client.post(
        "/users/",
        json={"email": "test@example.com", "name": "Test User"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

@pytest.mark.asyncio
async def test_get_nonexistent_user(async_client: AsyncClient):
    response = await async_client.get("/users/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
```

### Pattern 5: Mocking External Services

Mock HTTP calls with respx or similar.

```python
import respx
from httpx import Response

@respx.mock
async def test_external_api_call(async_client: AsyncClient):
    route = respx.get("https://api.external.com/data").mock(
        return_value=Response(200, json={"result": "success"})
    )
    
    response = await async_client.post("/process-external/")
    
    assert response.status_code == 200
    assert route.called
```

### Pattern 6: Testing Authentication

Test protected endpoints.

```python
@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-token"}

@pytest.mark.asyncio
async def test_protected_endpoint(async_client: AsyncClient, auth_headers):
    response = await async_client.get(
        "/admin/users",
        headers=auth_headers
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_protected_without_auth(async_client: AsyncClient):
    response = await async_client.get("/admin/users")
    assert response.status_code == 401
```

## Best Practices

1. **Use AsyncClient for async apps** - TestClient is sync-only
2. **Override dependencies per test** - Don't share state between tests
3. **Use transaction rollback** - Faster than drop/create
4. **Mock external services** - Don't hit real APIs in tests
5. **Test status codes AND response bodies** - Verify shape and content
6. **Use factories for test data** - factories-boy or similar
7. **Separate unit and integration tests** - Mark with pytest markers
8. **Test error cases** - 400s, 404s, 500s should all be tested
