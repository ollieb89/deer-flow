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
