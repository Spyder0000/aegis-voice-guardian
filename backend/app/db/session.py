"""SQLAlchemy engine and request-scoped session management."""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def _create_engine(database_url: str) -> Engine | None:
    if not database_url:
        return None

    options: dict[str, object] = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **options)


engine = _create_engine(DATABASE_URL)
SessionLocal = (
    sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    if engine is not None
    else None
)


def get_db() -> Generator[Session | None, None, None]:
    """Yield a DB session when configured, otherwise enable demo-memory mode."""
    if SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine: Engine | None = None) -> None:
    """Create ORM tables for local/test databases.

    Production/demo Compose initializes PostgreSQL from ``schema.sql``. This
    helper keeps tests and ad-hoc environments reproducible.
    """
    selected_engine = target_engine or engine
    if selected_engine is None:
        return

    # Register all model metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=selected_engine)
