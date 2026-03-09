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
