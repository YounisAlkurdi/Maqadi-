"""Unit tests for items use cases, sorting, ETag, and duplicate handling."""

import pytest

from app.application.items import (
    AddItem,
    ArchiveBought,
    ListItems,
    SetStatus,
    UpdateItem,
)
from app.domain.enums import Category, ItemStatus, Urgency
from app.domain.errors import (
    DuplicateItemError,
    InvalidTransitionError,
    NotFoundError,
    ValidationError,
)
from tests.unit.fakes import FakeClock, FakeEventBus, FakeItemRepo


async def test_add_item_normalizes_and_detects_duplicate() -> None:
    repo = FakeItemRepo()
    clock = FakeClock()
    bus = FakeEventBus()
    add_uc = AddItem(repo, clock, bus)

    created = await add_uc.execute(
        household_id="hh-1",
        member_id="m-1",
        name="  بندورة  ",
        quantity_text="كيلو",
        category=Category.PRODUCE,
    )
    assert created.name == "بندورة"
    assert created.name_normalized == "بندوره"
    assert created.requested_by_member_id == "m-1"
    assert len(bus.events) == 1
    assert bus.events[0][1] == "item.created"

    # Different spelling/diacritics -> same normalized name -> 409 DuplicateItemError
    with pytest.raises(DuplicateItemError) as exc_info:
        await add_uc.execute(
            household_id="hh-1",
            member_id="m-2",
            name="بَنْدُورَة",
        )
    assert exc_info.value.existing_item_id == created.id


async def test_add_item_rejects_empty_name() -> None:
    add_uc = AddItem(FakeItemRepo(), FakeClock())
    with pytest.raises(ValidationError):
        await add_uc.execute(household_id="hh-1", member_id="m-1", name="   ")


async def test_list_items_sorting_and_etag() -> None:
    repo = FakeItemRepo()
    clock = FakeClock()
    add_uc = AddItem(repo, clock)
    status_uc = SetStatus(repo, clock)
    list_uc = ListItems(repo)

    i_normal_1 = await add_uc.execute(
        household_id="hh-1", member_id="m-1", name="خبز", urgency=Urgency.NORMAL
    )
    clock.advance(minutes=1)
    i_bought = await add_uc.execute(
        household_id="hh-1", member_id="m-1", name="لبن", urgency=Urgency.URGENT
    )
    clock.advance(minutes=1)
    i_urgent = await add_uc.execute(
        household_id="hh-1", member_id="m-1", name="بيض", urgency=Urgency.URGENT
    )
    clock.advance(minutes=1)
    await status_uc.execute(
        household_id="hh-1", item_id=i_bought.id, member_id="m-2", status=ItemStatus.BOUGHT
    )

    res = await list_uc.execute(household_id="hh-1")
    assert [i.id for i in res.items] == [i_urgent.id, i_normal_1.id, i_bought.id]
    assert res.etag.startswith('"3:')


async def test_update_item_and_cross_household_not_found() -> None:
    repo = FakeItemRepo()
    clock = FakeClock()
    add_uc = AddItem(repo, clock)
    update_uc = UpdateItem(repo, clock)

    item = await add_uc.execute(household_id="hh-1", member_id="m-1", name="لبن")
    clock.advance(minutes=2)
    updated = await update_uc.execute(
        household_id="hh-1",
        item_id=item.id,
        quantity_text="علبتين",
        urgency=Urgency.URGENT,
    )
    assert updated.quantity_text == "علبتين"
    assert updated.urgency == Urgency.URGENT
    assert updated.updated_at > item.updated_at

    with pytest.raises(NotFoundError):
        await update_uc.execute(household_id="hh-2", item_id=item.id, name="حليب")


async def test_set_status_and_archive_bought() -> None:
    repo = FakeItemRepo()
    clock = FakeClock()
    add_uc = AddItem(repo, clock)
    status_uc = SetStatus(repo, clock)
    archive_uc = ArchiveBought(repo, clock)
    list_uc = ListItems(repo)

    item = await add_uc.execute(household_id="hh-1", member_id="m-1", name="شاي")
    bought = await status_uc.execute(
        household_id="hh-1", item_id=item.id, member_id="m-2", status=ItemStatus.BOUGHT
    )
    assert bought.bought_by_member_id == "m-2"
    assert bought.bought_at is not None

    with pytest.raises(InvalidTransitionError):
        await status_uc.execute(
            household_id="hh-1", item_id=item.id, member_id="m-2", status=ItemStatus.CANCELLED
        )

    archived_count = await archive_uc.execute(household_id="hh-1", older_than_hours=0)
    assert archived_count == 1

    res = await list_uc.execute(household_id="hh-1")
    assert res.items == []
