"""In-memory fake adapters for unit tests."""

from dataclasses import replace
from datetime import UTC, datetime
from typing import Any

from app.domain.entities import Household, Item, Member
from app.domain.enums import ItemStatus
from app.domain.errors import DuplicateItemError, NotFoundError


class FakeClock:
    def __init__(self, initial: datetime | None = None) -> None:
        self._now = initial or datetime(2026, 11, 27, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, **kwargs: Any) -> datetime:
        from datetime import timedelta

        self._now = self._now + timedelta(**kwargs)
        return self._now


class FakeHouseholdRepo:
    def __init__(self) -> None:
        self._by_id: dict[str, Household] = {}

    async def create(self, household: Household) -> Household:
        for existing in self._by_id.values():
            if existing.invite_code == household.invite_code:
                raise ValueError("Duplicate invite_code")
        self._by_id[household.id] = household
        return household

    async def get_by_id(self, household_id: str) -> Household | None:
        return self._by_id.get(household_id)

    async def get_by_invite_code(self, invite_code: str) -> Household | None:
        for household in self._by_id.values():
            if household.invite_code == invite_code:
                return household
        return None

    async def update_invite_code(self, household_id: str, new_code: str) -> Household:
        household = self._by_id.get(household_id)
        if household is None:
            raise NotFoundError("Household not found")
        updated = replace(household, invite_code=new_code)
        self._by_id[household_id] = updated
        return updated


class FakeMemberRepo:
    def __init__(self) -> None:
        self._by_id: dict[str, Member] = {}

    async def create(self, member: Member) -> Member:
        self._by_id[member.id] = member
        return member

    async def get_by_id(self, member_id: str) -> Member | None:
        return self._by_id.get(member_id)

    async def get_by_token_hash(self, token_hash: str) -> Member | None:
        for member in self._by_id.values():
            if member.token_hash == token_hash:
                return member
        return None

    async def list_by_household(self, household_id: str) -> list[Member]:
        return sorted(
            (m for m in self._by_id.values() if m.household_id == household_id),
            key=lambda m: m.created_at,
        )


class FakeItemRepo:
    def __init__(self) -> None:
        self._by_id: dict[str, Item] = {}

    async def create(self, item: Item) -> Item:
        if item.status == ItemStatus.OPEN and item.archived_at is None:
            existing = await self.find_open_by_normalized_name(
                item.household_id, item.name_normalized
            )
            if existing is not None:
                raise DuplicateItemError(existing_item_id=existing.id)
        self._by_id[item.id] = item
        return item

    async def get_by_id(self, household_id: str, item_id: str) -> Item | None:
        item = self._by_id.get(item_id)
        if item is None or item.household_id != household_id:
            return None
        return item

    async def find_open_by_normalized_name(
        self, household_id: str, name_normalized: str
    ) -> Item | None:
        for item in self._by_id.values():
            if (
                item.household_id == household_id
                and item.name_normalized == name_normalized
                and item.status == ItemStatus.OPEN
                and item.archived_at is None
            ):
                return item
        return None

    async def list_by_household(
        self,
        household_id: str,
        *,
        status: ItemStatus | None = None,
        include_archived: bool = False,
    ) -> list[Item]:
        results = [i for i in self._by_id.values() if i.household_id == household_id]
        if status is not None:
            results = [i for i in results if i.status == status]
        if not include_archived:
            results = [i for i in results if i.archived_at is None]
        return results

    async def update(self, item: Item) -> Item:
        existing = await self.get_by_id(item.household_id, item.id)
        if existing is None:
            raise NotFoundError("Item not found")
        if item.status == ItemStatus.OPEN and item.archived_at is None:
            conflict = await self.find_open_by_normalized_name(
                item.household_id, item.name_normalized
            )
            if conflict is not None and conflict.id != item.id:
                raise DuplicateItemError(existing_item_id=conflict.id)
        self._by_id[item.id] = item
        return item

    async def archive_bought_before(
        self, household_id: str, cutoff: datetime, now: datetime
    ) -> int:
        count = 0
        for item_id, item in list(self._by_id.items()):
            if (
                item.household_id == household_id
                and item.status == ItemStatus.BOUGHT
                and item.archived_at is None
                and item.bought_at is not None
                and item.bought_at <= cutoff
            ):
                self._by_id[item_id] = replace(item, archived_at=now, updated_at=now)
                count += 1
        return count

    async def list_recent_bought(self, household_id: str, limit: int) -> list[Item]:
        bought = [
            i
            for i in self._by_id.values()
            if i.household_id == household_id
            and i.status == ItemStatus.BOUGHT
            and i.bought_at is not None
        ]
        bought.sort(key=lambda i: i.bought_at or datetime.min.replace(tzinfo=UTC), reverse=True)
        return bought[:limit]


class FakeEventBus:
    def __init__(self) -> None:
        self.events: list[tuple[str, str, dict[str, Any]]] = []

    async def publish(self, household_id: str, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append((household_id, event_type, payload))
