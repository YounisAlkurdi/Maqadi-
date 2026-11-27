"""Unit tests for item status transition rules."""

from datetime import UTC, datetime

import pytest

from app.domain.entities import Item
from app.domain.enums import Category, ItemSource, ItemStatus, Urgency
from app.domain.errors import InvalidTransitionError


def _make_item(status: ItemStatus) -> Item:
    now = datetime(2026, 11, 27, 10, 0, tzinfo=UTC)
    return Item(
        id="item-1",
        household_id="hh-1",
        name="لبن",
        name_normalized="لبن",
        quantity_text=None,
        note=None,
        category=Category.DAIRY_EGGS,
        status=status,
        urgency=Urgency.NORMAL,
        requested_by_member_id="mem-1",
        bought_by_member_id="mem-2" if status == ItemStatus.BOUGHT else None,
        source=ItemSource.MANUAL,
        created_at=now,
        updated_at=now,
        bought_at=now if status == ItemStatus.BOUGHT else None,
        archived_at=None,
    )


def test_open_to_bought_sets_bought_fields() -> None:
    later = datetime(2026, 11, 27, 11, 0, tzinfo=UTC)
    updated = _make_item(ItemStatus.OPEN).transition_to(
        ItemStatus.BOUGHT, actor_member_id="mem-2", now=later
    )
    assert updated.status == ItemStatus.BOUGHT
    assert updated.bought_by_member_id == "mem-2"
    assert updated.bought_at == later
    assert updated.updated_at == later


def test_open_to_cancelled_clears_bought_fields() -> None:
    later = datetime(2026, 11, 27, 11, 0, tzinfo=UTC)
    updated = _make_item(ItemStatus.OPEN).transition_to(
        ItemStatus.CANCELLED, actor_member_id="mem-1", now=later
    )
    assert updated.status == ItemStatus.CANCELLED
    assert updated.bought_by_member_id is None
    assert updated.bought_at is None
    assert updated.updated_at == later


def test_bought_to_open_undo_clears_bought_fields() -> None:
    later = datetime(2026, 11, 27, 11, 0, tzinfo=UTC)
    updated = _make_item(ItemStatus.BOUGHT).transition_to(
        ItemStatus.OPEN, actor_member_id="mem-1", now=later
    )
    assert updated.status == ItemStatus.OPEN
    assert updated.bought_by_member_id is None
    assert updated.bought_at is None
    assert updated.updated_at == later


def test_cancelled_to_open_restores_item() -> None:
    later = datetime(2026, 11, 27, 11, 0, tzinfo=UTC)
    updated = _make_item(ItemStatus.CANCELLED).transition_to(
        ItemStatus.OPEN, actor_member_id="mem-1", now=later
    )
    assert updated.status == ItemStatus.OPEN
    assert updated.updated_at == later


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (ItemStatus.OPEN, ItemStatus.OPEN),
        (ItemStatus.BOUGHT, ItemStatus.BOUGHT),
        (ItemStatus.BOUGHT, ItemStatus.CANCELLED),
        (ItemStatus.CANCELLED, ItemStatus.CANCELLED),
        (ItemStatus.CANCELLED, ItemStatus.BOUGHT),
    ],
)
def test_illegal_status_transitions_raise(current: ItemStatus, target: ItemStatus) -> None:
    later = datetime(2026, 11, 27, 11, 0, tzinfo=UTC)
    with pytest.raises(InvalidTransitionError):
        _make_item(current).transition_to(target, actor_member_id="mem-1", now=later)
