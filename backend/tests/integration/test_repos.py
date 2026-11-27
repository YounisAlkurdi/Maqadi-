"""Integration tests for SQLite repositories, WAL/FK pragmas, and unique constraints."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.domain.entities import Household, Item, Member
from app.domain.enums import Category, ItemSource, ItemStatus, Urgency
from app.domain.errors import DuplicateItemError
from app.infrastructure.db import create_db_engine, create_session_factory, init_db
from app.infrastructure.repos import SqlHouseholdRepo, SqlItemRepo, SqlMemberRepo


@pytest.fixture
async def db_session_factory(tmp_path: Path):
    db_file = tmp_path / "test_maqadi.db"
    engine = create_db_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)
    factory = create_session_factory(engine)
    yield engine, factory
    await engine.dispose()


async def test_sqlite_pragmas_wal_and_foreign_keys(db_session_factory) -> None:
    engine, _ = db_session_factory
    async with engine.connect() as conn:
        journal = (await conn.execute(text("PRAGMA journal_mode;"))).scalar_one()
        fk = (await conn.execute(text("PRAGMA foreign_keys;"))).scalar_one()
    assert str(journal).lower() == "wal"
    assert fk == 1


async def test_household_crud_and_unique_invite_code(db_session_factory) -> None:
    _, factory = db_session_factory
    repo = SqlHouseholdRepo(factory)
    now = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)

    hh = Household(id="hh-1", name="بيت أبو أحمد", invite_code="K7M29QXP", created_at=now)
    created = await repo.create(hh)
    assert created == hh

    fetched = await repo.get_by_id("hh-1")
    assert fetched == hh

    by_code = await repo.get_by_invite_code("K7M29QXP")
    assert by_code == hh

    rotated = await repo.update_invite_code("hh-1", "NEW8CODE")
    assert rotated.invite_code == "NEW8CODE"
    assert await repo.get_by_invite_code("K7M29QXP") is None

    duplicate = Household(id="hh-2", name="بيت آخر", invite_code="NEW8CODE", created_at=now)
    with pytest.raises(IntegrityError):
        await repo.create(duplicate)


async def test_member_crud_and_lookup_by_token_hash(db_session_factory) -> None:
    _, factory = db_session_factory
    hh_repo = SqlHouseholdRepo(factory)
    mem_repo = SqlMemberRepo(factory)
    now = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)

    await hh_repo.create(
        Household(id="hh-1", name="بيت أبو أحمد", invite_code="K7M29QXP", created_at=now)
    )
    m1 = Member(
        id="m-1",
        household_id="hh-1",
        display_name="أمي",
        color="#2A7F85",
        token_hash="hash-1",
        created_at=now,
    )
    m2 = Member(
        id="m-2",
        household_id="hh-1",
        display_name="يونس",
        color="#7A4A7D",
        token_hash="hash-2",
        created_at=now + timedelta(minutes=1),
    )
    await mem_repo.create(m1)
    await mem_repo.create(m2)

    assert await mem_repo.get_by_token_hash("hash-1") == m1
    assert await mem_repo.list_by_household("hh-1") == [m1, m2]


async def test_item_crud_and_partial_unique_index(db_session_factory) -> None:
    _, factory = db_session_factory
    hh_repo = SqlHouseholdRepo(factory)
    item_repo = SqlItemRepo(factory)
    now = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)

    await hh_repo.create(Household(id="hh-1", name="بيت 1", invite_code="CODE1111", created_at=now))
    await hh_repo.create(Household(id="hh-2", name="بيت 2", invite_code="CODE2222", created_at=now))

    item1 = Item(
        id="item-1",
        household_id="hh-1",
        name="بندورة",
        name_normalized="بندوره",
        quantity_text="كيلو",
        note=None,
        category=Category.PRODUCE,
        status=ItemStatus.OPEN,
        urgency=Urgency.NORMAL,
        requested_by_member_id=None,
        bought_by_member_id=None,
        source=ItemSource.MANUAL,
        created_at=now,
        updated_at=now,
    )
    await item_repo.create(item1)

    # Duplicate open item in same household is rejected at DB level
    dup = Item(
        id="item-2",
        household_id="hh-1",
        name="بندورة",
        name_normalized="بندوره",
        quantity_text="2 كيلو",
        note=None,
        category=Category.PRODUCE,
        status=ItemStatus.OPEN,
        urgency=Urgency.NORMAL,
        requested_by_member_id=None,
        bought_by_member_id=None,
        source=ItemSource.MANUAL,
        created_at=now,
        updated_at=now,
    )
    with pytest.raises(DuplicateItemError):
        await item_repo.create(dup)

    # Same normalized name in a different household is allowed
    other_hh_item = Item(
        id="item-3",
        household_id="hh-2",
        name="بندورة",
        name_normalized="بندوره",
        quantity_text=None,
        note=None,
        category=Category.PRODUCE,
        status=ItemStatus.OPEN,
        urgency=Urgency.NORMAL,
        requested_by_member_id=None,
        bought_by_member_id=None,
        source=ItemSource.MANUAL,
        created_at=now,
        updated_at=now,
    )
    await item_repo.create(other_hh_item)

    # Mark item-1 as bought -> another open item with same name_normalized is now allowed
    bought_item = item1.transition_to(
        ItemStatus.BOUGHT, actor_member_id=None, now=now + timedelta(minutes=5)
    )
    await item_repo.update(bought_item)
    await item_repo.create(dup)

    open_items = await item_repo.list_by_household("hh-1", status=ItemStatus.OPEN)
    assert len(open_items) == 1
    assert open_items[0].id == "item-2"
