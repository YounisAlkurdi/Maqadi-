"""Composition root: wires concrete infrastructure adapters to application ports."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI

from app.application.households import (
    CreateHousehold,
    GetMe,
    JoinHousehold,
    RotateInviteCode,
)
from app.config import Settings
from app.infrastructure.clock import SystemClock
from app.infrastructure.db import create_db_engine, create_session_factory, init_db
from app.infrastructure.rate_limit import InMemoryRateLimiter
from app.infrastructure.repos import SqlHouseholdRepo, SqlItemRepo, SqlMemberRepo


@dataclass
class AppContainer:
    household_repo: SqlHouseholdRepo
    member_repo: SqlMemberRepo
    item_repo: SqlItemRepo
    clock: SystemClock
    rate_limiter: InMemoryRateLimiter
    create_household: CreateHousehold
    join_household: JoinHousehold
    rotate_invite_code: RotateInviteCode
    get_me: GetMe


def build_container(settings: Settings) -> tuple[AppContainer, object]:
    """Instantiate infrastructure adapters and wire application use cases."""
    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    household_repo = SqlHouseholdRepo(session_factory)
    member_repo = SqlMemberRepo(session_factory)
    item_repo = SqlItemRepo(session_factory)
    clock = SystemClock()
    rate_limiter = InMemoryRateLimiter(clock)

    container = AppContainer(
        household_repo=household_repo,
        member_repo=member_repo,
        item_repo=item_repo,
        clock=clock,
        rate_limiter=rate_limiter,
        create_household=CreateHousehold(household_repo, member_repo, clock),
        join_household=JoinHousehold(household_repo, member_repo, rate_limiter, clock),
        rotate_invite_code=RotateInviteCode(household_repo),
        get_me=GetMe(member_repo),
    )
    return container, engine


def create_lifespan(settings: Settings):
    """Create FastAPI lifespan handler that initializes and disposes the DB engine."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        container, engine = build_container(settings)
        await init_db(engine)
        app.state.container = container
        app.state.db_engine = engine
        try:
            yield
        finally:
            await engine.dispose()

    return lifespan
