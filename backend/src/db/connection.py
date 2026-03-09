"""Database connection management.
"""

import logging
import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

# Default database URL - uses SQLite for simplicity
DEFAULT_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./deerflow.db"
)

_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            DEFAULT_DATABASE_URL,
            connect_args={"check_same_thread": False} if "sqlite" in DEFAULT_DATABASE_URL else {},
            echo=os.environ.get("SQL_ECHO", "false").lower() == "true",
        )
    return _engine


def get_sessionmaker():
    """Get or create the session maker."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


@contextmanager
def get_db_session():
    """Get a database session as a context manager.
    
    Example:
        >>> with get_db_session() as session:
        ...     models = session.query(KilocodeModel).all()
    """
    SessionLocal = get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """Initialize the database, creating all tables."""
    from .models import Base
    
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=get_engine())
    logger.info("Database initialized successfully")


def close_db():
    """Close the database connection."""
    global _engine
    if _engine:
        _engine.dispose()
        _engine = None
        logger.info("Database connection closed")
