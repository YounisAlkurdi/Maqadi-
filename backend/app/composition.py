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
from app.application.items import (
    AddItem,
    ArchiveBought,
    ListItems,
    ListRecentBought,
    SetStatus,
    UpdateItem,
)
from app.application.paste_import import ConfirmPaste, PreviewPaste
from app.config import Settings
from app.infrastructure.clock import SystemClock
from app.infrastructure.db import create_db_engine, create_session_factory, init_db
from app.infrastructure.extractors.chain import ChainExtractor
from app.infrastructure.extractors.llm import LLMItemExtractor
from app.infrastructure.extractors.rules import RuleBasedExtractor
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
    list_items: ListItems
    add_item: AddItem
    update_item: UpdateItem
    set_status: SetStatus
    archive_bought: ArchiveBought
    list_recent_bought: ListRecentBought
    preview_paste: PreviewPaste
    confirm_paste: ConfirmPaste


def build_container(settings: Settings) -> tuple[AppContainer, object]:
    """Instantiate infrastructure adapters and wire application use cases."""
    engine = create_db_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    household_repo = SqlHouseholdRepo(session_factory)
    member_repo = SqlMemberRepo(session_factory)
    item_repo = SqlItemRepo(session_factory)
    clock = SystemClock()
    rate_limiter = InMemoryRateLimiter(clock)
    rules_extractor = RuleBasedExtractor()
    llm_extractor = (
        LLMItemExtractor(
            provider=settings.llm_provider,
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
        if settings.llm_provider.lower().strip() != "none" and settings.llm_api_key
        else None
    )
    extractor = ChainExtractor(primary=llm_extractor, fallback=rules_extractor)

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
        list_items=ListItems(item_repo),
        add_item=AddItem(item_repo, clock),
        update_item=UpdateItem(item_repo, clock),
        set_status=SetStatus(item_repo, clock),
        archive_bought=ArchiveBought(item_repo, clock),
        list_recent_bought=ListRecentBought(item_repo),
        preview_paste=PreviewPaste(
            extractor, item_repo, member_repo, max_paste_chars=settings.max_paste_chars
        ),
        confirm_paste=ConfirmPaste(item_repo, member_repo, clock),
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
