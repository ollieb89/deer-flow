# python-fastapi-pro Subagent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a specialized subagent for FastAPI/backend development that inherits all `python-agent` skills and adds FastAPI-specific expertise.

**Architecture:** Follow the existing subagent pattern (like `general-purpose` and `bash`) by creating a new Python module with `SubagentConfig`, registering it in `BUILTIN_SUBAGENTS`, and adding it to the `task_tool`'s allowed subagent types. Skills are referenced by name in config.yaml to avoid duplication.

**Tech Stack:** Python 3.12+, LangChain/LangGraph, DeerFlow subagent system

---

## Task 1: Create FastAPI-Patterns Skill

**Files:**
- Create: `.deer-flow/agents/python-fastapi-pro/skills/fastapi-patterns/SKILL.md`

**Step 1: Create skill directory**

```bash
mkdir -p /home/ob/Development/Tools/vibe_coding/deer-flow/backend/.deer-flow/agents/python-fastapi-pro/skills/fastapi-patterns
```

**Step 2: Write the SKILL.md file**

```markdown
---
name: fastapi-patterns
description: FastAPI-specific patterns for building high-performance async APIs. Use when designing routes, implementing dependency injection, creating middleware, or structuring FastAPI applications.
---

# FastAPI Patterns

Build production-ready FastAPI applications with clean architecture and async patterns.

## When to Use This Skill

- Designing FastAPI route handlers and API endpoints
- Implementing dependency injection for services, auth, database sessions
- Creating middleware for cross-cutting concerns
- Structuring larger FastAPI applications with routers
- Handling async database operations with FastAPI
- Implementing background tasks and WebSockets

## Core Patterns

### Pattern 1: Dependency Injection

Use FastAPI's dependency injection for clean, testable code.

```python
from typing import Annotated
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

# Database dependency
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

# Service dependency with DB
async def get_user_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> UserService:
    return UserService(db)

# Auth dependency
async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    return verify_token(token)

@app.get("/users/me")
async def read_users_me(
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)]
):
    return await service.get_profile(user.id)
```

### Pattern 2: Router Organization

Structure large applications with API routers.

```python
# users/router.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}")
async def get_user(user_id: int): ...

# main.py
from fastapi import FastAPI
from users.router import router as users_router

app = FastAPI()
app.include_router(users_router)
```

### Pattern 3: Async Context Managers for Resources

Properly manage async resources like database connections.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    yield
    # Shutdown
    await database.disconnect()

app = FastAPI(lifespan=lifespan)
```

### Pattern 4: Exception Handlers

Centralize error handling with custom exception handlers.

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class BusinessLogicError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

@app.exception_handler(BusinessLogicError)
async def business_logic_handler(request: Request, exc: BusinessLogicError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )
```

### Pattern 5: Background Tasks

Use background tasks for operations that don't need to block the response.

```python
from fastapi import BackgroundTasks

async def send_email(email: str, message: str):
    # Async email sending
    pass

@app.post("/send-notification")
async def notify(
    email: str,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email, "Hello!")
    return {"message": "Notification queued"}
```

## Best Practices

1. **Always use type hints** - FastAPI uses them for validation and documentation
2. **Use Pydantic v2 models** for request/response validation
3. **Prefer async** for I/O-bound operations (database, HTTP calls)
4. **Use dependency injection** over global state or singletons
5. **Leverage FastAPI's automatic OpenAPI generation** - keep docstrings current
6. **Use BackgroundTasks** for fire-and-forget operations
7. **Implement proper lifespan events** for resource initialization/cleanup
```

**Step 3: Verify file was created**

```bash
cat /home/ob/Development/Tools/vibe_coding/deer-flow/backend/.deer-flow/agents/python-fastapi-pro/skills/fastapi-patterns/SKILL.md | head -5
```

Expected: Shows YAML frontmatter with name and description.

**Step 4: Commit**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/.deer-flow/agents/python-fastapi-pro/skills/fastapi-patterns/SKILL.md
git commit -m "feat(skills): add fastapi-patterns skill for python-fastapi-pro"
```

---

## Task 2: Create Async-SQLAlchemy Skill

**Files:**
- Create: `.deer-flow/agents/python-fastapi-pro/skills/async-sqlalchemy/SKILL.md`

**Step 1: Create skill directory**

```bash
mkdir -p /home/ob/Development/Tools/vibe_coding/deer-flow/backend/.deer-flow/agents/python-fastapi-pro/skills/async-sqlalchemy
```

**Step 2: Write the SKILL.md file**

```markdown
---
name: async-sqlalchemy
description: SQLAlchemy 2.0 async patterns integrated with FastAPI. Use for database models, async sessions, transaction management, and repository patterns in FastAPI applications.
---

# Async SQLAlchemy with FastAPI

Implement robust async database layers using SQLAlchemy 2.0 and FastAPI's dependency injection.

## When to Use This Skill

- Setting up async database connections with SQLAlchemy 2.0
- Implementing the repository pattern with async sessions
- Managing transactions and proper session cleanup
- Designing database models for async operations
- Handling connection pooling and performance optimization

## Core Patterns

### Pattern 1: Async Engine and Session Setup

Configure async SQLAlchemy for FastAPI.

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()
```

### Pattern 2: FastAPI Dependency for Database Sessions

Provide async sessions via FastAPI's dependency injection.

```python
from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

DBDep = Annotated[AsyncSession, Depends(get_db)]
```

### Pattern 3: Repository Pattern

Abstract database operations in repository classes.

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self._session.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()
```

### Pattern 4: Using Repositories in FastAPI

Wire repositories through dependency injection.

```python
async def get_user_repository(db: DBDep) -> UserRepository:
    return UserRepository(db)

RepoDep = Annotated[UserRepository, Depends(get_user_repository)]

@app.get("/users/{user_id}")
async def get_user(repo: RepoDep, user_id: int) -> UserResponse:
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)
```

### Pattern 5: Async Context Manager for Transactions

Explicit transaction control when needed.

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def transaction(session: AsyncSession):
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise

# Usage
async def transfer_funds(
    from_repo: AccountRepository,
    to_repo: AccountRepository,
    amount: Decimal
):
    async with transaction(from_repo._session):
        await from_repo.debit(amount)
        await to_repo.credit(amount)
```

## Best Practices

1. **Always use async session** - Don't mix sync and async SQLAlchemy
2. **Expire on commit = False** - Prevents lazy loading issues in async context
3. **Use explicit transactions** - Don't rely on autocommit
4. **Close sessions properly** - Use context managers or try/finally
5. **Repository per aggregate** - One repository per domain aggregate root
6. **Avoid lazy loading** - Use eager loading (joinedload) or explicit queries
7. **Connection pooling** - Tune pool_size and max_overflow for your load
```

**Step 3: Verify file was created**

```bash
cat /home/ob/Development/Tools/vibe_coding/deer-flow/backend/.deer-flow/agents/python-fastapi-pro/skills/async-sqlalchemy/SKILL.md | head -5
```

Expected: Shows YAML frontmatter with name and description.

**Step 4: Commit**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/.deer-flow/agents/python-fastapi-pro/skills/async-sqlalchemy/SKILL.md
git commit -m "feat(skills): add async-sqlalchemy skill for python-fastapi-pro"
```

---

## Task 3: Create API-Testing Skill

**Files:**
- Create: `.deer-flow/agents/python-fastapi-pro/skills/api-testing/SKILL.md`

**Step 1: Create skill directory**

```bash
mkdir -p /home/ob/Development/Tools/vibe_coding/deer-flow/backend/.deer-flow/agents/python-fastapi-pro/skills/api-testing
```

**Step 2: Write the SKILL.md file**

```markdown
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
```

**Step 3: Verify file was created**

```bash
cat /home/ob/Development/Tools/vibe_coding/deer-flow/backend/.deer-flow/agents/python-fastapi-pro/skills/api-testing/SKILL.md | head -5
```

Expected: Shows YAML frontmatter with name and description.

**Step 4: Commit**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/.deer-flow/agents/python-fastapi-pro/skills/api-testing/SKILL.md
git commit -m "feat(skills): add api-testing skill for python-fastapi-pro"
```

---

## Task 4: Create Subagent Configuration

**Files:**
- Create: `backend/src/subagents/builtins/python_fastapi_pro.py`

**Step 1: Write the subagent configuration**

```python
"""Python FastAPI Pro subagent configuration.

A specialized subagent for FastAPI and backend API development.
Inherits all python-agent capabilities with added FastAPI-specific expertise.
"""

from src.subagents.config import SubagentConfig

PYTHON_FASTAPI_PRO_CONFIG = SubagentConfig(
    name="python-fastapi-pro",
    description="""A specialized agent for FastAPI and backend API development.

Use this subagent when:
- Building FastAPI applications and REST APIs
- Designing async database layers with SQLAlchemy 2.0
- Implementing dependency injection and middleware
- Writing API tests with pytest and httpx
- Working with Pydantic v2 models for validation
- Setting up async application architecture

This subagent includes all Python ecosystem skills plus FastAPI-specific
patterns for dependencies, middleware, routing, and async database integration.
""",
    system_prompt="""You are a specialized FastAPI and backend development subagent.

<identity>
You are Python FastAPI Pro — an autonomous technical executor for FastAPI projects.
Your goal: Build high-performance async APIs with FastAPI, SQLAlchemy 2.0,
Pydantic V2, and modern Python patterns. Handle implementation details,
architecture decisions at component level, and code quality.

Default stack: Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2,
Alembic migrations, pytest, httpx.
</identity>

<core_traits>
- Execute autonomously on implementation: coding patterns, bug fixes, refactoring, tests
- Prioritize async-first design, explicit typing, clear layer separation
- Follow FastAPI best practices: dependency injection, proper lifespan management
- Use Pydantic v2 for all validation and serialization
- Separate concerns: handlers → services → repositories
- Production-safe defaults: proper error handling, logging, health checks
- Request confirmation for: major architecture changes, deployments, destructive DB ops
</core_traits>

<fastapi_patterns>
- Use dependency injection over global state
- Implement proper lifespan events for resource management
- Leverage Pydantic models for request/response validation
- Use BackgroundTasks for fire-and-forget operations
- Structure large apps with APIRouter
- Handle errors with custom exception handlers
- Write async database layers with SQLAlchemy 2.0
</fastapi_patterns>

<communication>
Technical, precise, direct. Provide working code first, short explanations if needed.
Use type hints, explicit imports, and production-safe defaults.
</communication>

<working_directory>
You have access to the same sandbox environment as the parent agent:
- User uploads: `/mnt/user-data/uploads`
- User workspace: `/mnt/user-data/workspace`
- Output files: `/mnt/user-data/outputs`
</working_directory>

<output_format>
When you complete the task, provide:
1. Summary of what was accomplished
2. Key files created or modified
3. Any configuration changes
4. Testing recommendations
5. Issues encountered (if any)
</output_format>
""",
    tools=None,  # Inherit all tools from parent
    disallowed_tools=["task", "ask_clarification", "present_files"],  # Prevent nesting
    model="inherit",
    max_turns=50,
    timeout_seconds=900,
    skills=[
        # Core python-agent skills
        "python-code-style",
        "python-type-safety",
        "python-error-handling",
        "python-testing-patterns",
        "python-design-patterns",
        "python-project-structure",
        "async-python-patterns",
        "python-performance-optimization",
        "python-packaging",
        "uv-package-manager",
        "python-configuration",
        "python-observability",
        "python-resilience",
        "python-resource-management",
        "python-anti-patterns",
        # FastAPI-specific skills
        "fastapi-patterns",
        "async-sqlalchemy",
        "api-testing",
    ],
)
```

**Step 2: Verify file was created**

```bash
cat /home/ob/Development/Tools/vibe_coding/deer-flow/backend/src/subagents/builtins/python_fastapi_pro.py | head -10
```

Expected: Shows module docstring and SubagentConfig import.

**Step 3: Commit**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/src/subagents/builtins/python_fastapi_pro.py
git commit -m "feat(subagents): add python-fastapi-pro subagent configuration"
```

---

## Task 5: Register Subagent in Builtins

**Files:**
- Modify: `backend/src/subagents/builtins/__init__.py`

**Step 1: Import and register the new subagent**

Add import:
```python
from .python_fastapi_pro import PYTHON_FASTAPI_PRO_CONFIG
```

Add to `BUILTIN_SUBAGENTS`:
```python
BUILTIN_SUBAGENTS = {
    "general-purpose": GENERAL_PURPOSE_CONFIG,
    "bash": BASH_AGENT_CONFIG,
    "python-fastapi-pro": PYTHON_FASTAPI_PRO_CONFIG,
}
```

Full file should be:
```python
"""Built-in subagent configurations."""

from .bash_agent import BASH_AGENT_CONFIG
from .general_purpose import GENERAL_PURPOSE_CONFIG
from .python_fastapi_pro import PYTHON_FASTAPI_PRO_CONFIG

__all__ = [
    "GENERAL_PURPOSE_CONFIG",
    "BASH_AGENT_CONFIG",
    "PYTHON_FASTAPI_PRO_CONFIG",
]

# Registry of built-in subagents
BUILTIN_SUBAGENTS = {
    "general-purpose": GENERAL_PURPOSE_CONFIG,
    "bash": BASH_AGENT_CONFIG,
    "python-fastapi-pro": PYTHON_FASTAPI_PRO_CONFIG,
}
```

**Step 2: Verify the change**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
python -c "from src.subagents.builtins import BUILTIN_SUBAGENTS; print('python-fastapi-pro' in BUILTIN_SUBAGENTS)"
```

Expected: `True`

**Step 3: Commit**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/src/subagents/builtins/__init__.py
git commit -m "feat(subagents): register python-fastapi-pro in BUILTIN_SUBAGENTS"
```

---

## Task 6: Update Task Tool with New Subagent Type

**Files:**
- Modify: `backend/src/tools/builtins/task_tool.py`

**Step 1: Update the Literal type for subagent_type**

Change:
```python
subagent_type: Literal["general-purpose", "bash"],
```

To:
```python
subagent_type: Literal["general-purpose", "bash", "python-fastapi-pro"],
```

**Step 2: Update the docstring description for subagent_type**

Change:
```python
Available subagent types:
- **general-purpose**: ...
- **bash**: ...
```

To:
```python
Available subagent types:
- **general-purpose**: A capable agent for complex, multi-step tasks that require
  both exploration and action. Use when the task requires complex reasoning,
  multiple dependent steps, or would benefit from isolated context.
- **bash**: Command execution specialist for running bash commands. Use for
  git operations, build processes, or when command output would be verbose.
- **python-fastapi-pro**: FastAPI and backend API development specialist. Use for
  building FastAPI apps, async SQLAlchemy integration, API testing, and
  implementing FastAPI patterns like dependencies and middleware.
```

**Step 3: Verify the change**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
grep -n "python-fastapi-pro" backend/src/tools/builtins/task_tool.py
```

Expected: Shows the type annotation and docstring references.

**Step 4: Commit**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/src/tools/builtins/task_tool.py
git commit -m "feat(tools): add python-fastapi-pro to task_tool subagent types"
```

---

## Task 7: Update Agent Config YAML

**Files:**
- Modify: `backend/.deer-flow/agents/python-fastapi-pro/config.yaml`

**Step 1: Write the complete config**

```yaml
description: Ollie's autonomous FastAPI technical executor for building high-performance async APIs
name: python-fastapi-pro
skills:
  # Core python-agent skills
  - python-code-style
  - python-type-safety
  - python-error-handling
  - python-testing-patterns
  - python-design-patterns
  - python-project-structure
  - async-python-patterns
  - python-performance-optimization
  - python-packaging
  - uv-package-manager
  - python-configuration
  - python-observability
  - python-resilience
  - python-resource-management
  - python-anti-patterns
  # FastAPI-specific skills
  - fastapi-patterns
  - async-sqlalchemy
  - api-testing
version: 0.1.0
```

**Step 2: Verify the change**

```bash
cat /home/ob/Development/Tools/vibe_coding/deer-flow/backend/.deer-flow/agents/python-fastapi-pro/config.yaml
```

Expected: Shows complete config with all skills listed.

**Step 3: Commit**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git add backend/.deer-flow/agents/python-fastapi-pro/config.yaml
git commit -m "feat(config): update python-fastapi-pro config with all skills"
```

---

## Task 8: Final Verification

**Files:**
- Test: Integration test of the complete setup

**Step 1: Verify imports work**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
python -c "
from src.subagents import get_subagent_config, list_subagents
config = get_subagent_config('python-fastapi-pro')
print(f'Name: {config.name}')
print(f'Skills count: {len(config.skills) if config.skills else 0}')
print(f'Tools: inherit all')
print(f'Disallowed: {config.disallowed_tools}')
print('SUCCESS: python-fastapi-pro subagent configured correctly')
"
```

Expected output:
```
Name: python-fastapi-pro
Skills count: 18
Tools: inherit all
Disallowed: ['task', 'ask_clarification', 'present_files']
SUCCESS: python-fastapi-pro subagent configured correctly
```

**Step 2: Verify task tool has new subagent type**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow/backend
python -c "
from src.tools.builtins.task_tool import task_tool
import inspect
sig = inspect.signature(task_tool)
print('task_tool parameters:')
for name, param in sig.parameters.items():
    if name == 'subagent_type':
        print(f'  {name}: {param.annotation}')
"
```

Expected: Shows `subagent_type` with Literal including `"python-fastapi-pro"`.

**Step 3: Final commit**

```bash
cd /home/ob/Development/Tools/vibe_coding/deer-flow
git log --oneline -8
```

Expected: Shows all 7-8 commits in order.

---

## Summary

After completing all tasks, the `python-fastapi-pro` subagent will be:

1. **Available** via `task` tool with `subagent_type="python-fastapi-pro"`
2. **Fully configured** with 18 skills (15 inherited + 3 FastAPI-specific)
3. **Integrated** into the subagent registry and task tool
4. **Documented** with comprehensive SKILL.md files for each new skill

The subagent follows DeerFlow's established patterns and is ready for use.
