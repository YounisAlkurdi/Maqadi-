"""Domain entities and status transition rules."""

from dataclasses import dataclass, replace
from datetime import datetime

from app.domain.enums import Category, ItemSource, ItemStatus, Urgency
from app.domain.errors import InvalidTransitionError

VALID_STATUS_TRANSITIONS: dict[ItemStatus, frozenset[ItemStatus]] = {
    ItemStatus.OPEN: frozenset({ItemStatus.BOUGHT, ItemStatus.CANCELLED}),
    ItemStatus.BOUGHT: frozenset({ItemStatus.OPEN}),
    ItemStatus.CANCELLED: frozenset({ItemStatus.OPEN}),
}


@dataclass(frozen=True)
class Household:
    id: str
    name: str
    invite_code: str
    created_at: datetime


@dataclass(frozen=True)
class Member:
    id: str
    household_id: str
    display_name: str
    color: str
    token_hash: str
    created_at: datetime


@dataclass(frozen=True)
class Item:
    id: str
    household_id: str
    name: str
    name_normalized: str
    quantity_text: str | None
    note: str | None
    category: Category
    status: ItemStatus
    urgency: Urgency
    requested_by_member_id: str | None
    bought_by_member_id: str | None
    source: ItemSource
    created_at: datetime
    updated_at: datetime
    bought_at: datetime | None = None
    archived_at: datetime | None = None

    def transition_to(
        self,
        target: ItemStatus,
        *,
        actor_member_id: str | None,
        now: datetime,
    ) -> "Item":
        """Return a new Item with the validated status transition applied."""
        allowed = VALID_STATUS_TRANSITIONS.get(self.status, frozenset())
        if target not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition item from '{self.status}' to '{target}'"
            )

        if target == ItemStatus.BOUGHT:
            return replace(
                self,
                status=ItemStatus.BOUGHT,
                bought_by_member_id=actor_member_id,
                bought_at=now,
                updated_at=now,
            )

        return replace(
            self,
            status=target,
            bought_by_member_id=None,
            bought_at=None,
            updated_at=now,
        )
