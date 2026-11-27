"""Composition root: wires concrete infrastructure adapters to application ports."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.infrastructure.db import create_db_engine, init_db


def create_lifespan(settings: Settings):
    """Create FastAPI lifespan handler that initializes and disposes the DB engine."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_db_engine(settings.database_url)
        await init_db(engine)
        app.state.db_engine = engine
        try:
            yield
        finally:
            await engine.dispose()

    return lifespan
