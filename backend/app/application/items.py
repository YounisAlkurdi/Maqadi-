"""Use cases for household shopping list items."""

import uuid
from dataclasses import dataclass, replace
from datetime import timedelta

from app.domain.entities import Item
from app.domain.enums import Category, ItemSource, ItemStatus, Urgency
from app.domain.errors import DuplicateItemError, NotFoundError, ValidationError
from app.domain.normalize import normalize_ar
from app.domain.ports import Clock, EventBus, ItemRepo

_UNSET = object()

_STATUS_ORDER: dict[ItemStatus, int] = {
    ItemStatus.OPEN: 0,
    ItemStatus.CANCELLED: 1,
    ItemStatus.BOUGHT: 2,
}

_URGENCY_ORDER: dict[Urgency, int] = {
    Urgency.URGENT: 0,
    Urgency.NORMAL: 1,
}


def validate_item_name(name: str) -> str:
    trimmed = name.strip()
    if not (1 <= len(trimmed) <= 120):
        raise ValidationError("Item name must be between 1 and 120 characters")
    return trimmed


def sort_items(items: list[Item]) -> list[Item]:
    """Sort items: open urgent first, then created_at ascending; bought at the end."""
    return sorted(
        items,
        key=lambda item: (
            _STATUS_ORDER.get(item.status, 9),
            _URGENCY_ORDER.get(item.urgency, 9),
            item.created_at,
        ),
    )


def compute_items_etag(items: list[Item]) -> str:
    """Compute an HTTP ETag from item count and max(updated_at)."""
    if not items:
        return '"0:none"'
    max_updated = max(item.updated_at for item in items)
    return f'"{len(items)}:{max_updated.isoformat()}"'


@dataclass(frozen=True)
class ListItemsResult:
    items: list[Item]
    etag: str


class ListItems:
    """List non-archived items for a household, sorted and tagged with an ETag."""

    def __init__(self, item_repo: ItemRepo) -> None:
        self._item_repo = item_repo

    async def execute(
        self,
        *,
        household_id: str,
        status: ItemStatus | None = None,
    ) -> ListItemsResult:
        items = await self._item_repo.list_by_household(
            household_id,
            status=status,
            include_archived=False,
        )
        sorted_items = sort_items(items)
        return ListItemsResult(items=sorted_items, etag=compute_items_etag(sorted_items))


class AddItem:
    """Add a new open item to the household list."""

    def __init__(
        self,
        item_repo: ItemRepo,
        clock: Clock,
        event_bus: EventBus | None = None,
    ) -> None:
        self._item_repo = item_repo
        self._clock = clock
        self._event_bus = event_bus

    async def execute(
        self,
        *,
        household_id: str,
        member_id: str,
        name: str,
        quantity_text: str | None = None,
        note: str | None = None,
        category: Category = Category.OTHER,
        urgency: Urgency = Urgency.NORMAL,
        source: ItemSource = ItemSource.MANUAL,
    ) -> Item:
        clean_name = validate_item_name(name)
        name_normalized = normalize_ar(clean_name)
        if not name_normalized:
            raise ValidationError("Item name cannot be empty")

        existing = await self._item_repo.find_open_by_normalized_name(household_id, name_normalized)
        if existing is not None:
            raise DuplicateItemError(
                "Item already exists in the open list",
                existing_item_id=existing.id,
            )

        now = self._clock.now()
        item = Item(
            id=str(uuid.uuid4()),
            household_id=household_id,
            name=clean_name,
            name_normalized=name_normalized,
            quantity_text=quantity_text.strip()
            if quantity_text and quantity_text.strip()
            else None,
            note=note.strip() if note and note.strip() else None,
            category=category,
            status=ItemStatus.OPEN,
            urgency=urgency,
            requested_by_member_id=member_id,
            bought_by_member_id=None,
            source=source,
            created_at=now,
            updated_at=now,
        )
        created = await self._item_repo.create(item)

        if self._event_bus is not None:
            await self._event_bus.publish(household_id, "item.created", {"item_id": created.id})

        return created


class UpdateItem:
    """Update editable fields of an existing household item."""

    def __init__(
        self,
        item_repo: ItemRepo,
        clock: Clock,
        event_bus: EventBus | None = None,
    ) -> None:
        self._item_repo = item_repo
        self._clock = clock
        self._event_bus = event_bus

    async def execute(
        self,
        *,
        household_id: str,
        item_id: str,
        name: str | object = _UNSET,
        quantity_text: str | None | object = _UNSET,
        note: str | None | object = _UNSET,
        category: Category | object = _UNSET,
        urgency: Urgency | object = _UNSET,
    ) -> Item:
        item = await self._item_repo.get_by_id(household_id, item_id)
        if item is None:
            raise NotFoundError("Item not found")

        new_name = item.name
        new_normalized = item.name_normalized
        if name is not _UNSET:
            assert isinstance(name, str)
            new_name = validate_item_name(name)
            new_normalized = normalize_ar(new_name)
            if not new_normalized:
                raise ValidationError("Item name cannot be empty")
            if item.status == ItemStatus.OPEN and new_normalized != item.name_normalized:
                conflict = await self._item_repo.find_open_by_normalized_name(
                    household_id, new_normalized
                )
                if conflict is not None and conflict.id != item.id:
                    raise DuplicateItemError(
                        "Item already exists in the open list",
                        existing_item_id=conflict.id,
                    )

        new_quantity = item.quantity_text
        if quantity_text is not _UNSET:
            assert quantity_text is None or isinstance(quantity_text, str)
            new_quantity = (
                quantity_text.strip() if quantity_text and quantity_text.strip() else None
            )

        new_note = item.note
        if note is not _UNSET:
            assert note is None or isinstance(note, str)
            new_note = note.strip() if note and note.strip() else None

        new_category = item.category
        if category is not _UNSET:
            assert isinstance(category, Category)
            new_category = category

        new_urgency = item.urgency
        if urgency is not _UNSET:
            assert isinstance(urgency, Urgency)
            new_urgency = urgency

        updated_item = replace(
            item,
            name=new_name,
            name_normalized=new_normalized,
            quantity_text=new_quantity,
            note=new_note,
            category=new_category,
            urgency=new_urgency,
            updated_at=self._clock.now(),
        )
        saved = await self._item_repo.update(updated_item)

        if self._event_bus is not None:
            await self._event_bus.publish(household_id, "item.updated", {"item_id": saved.id})

        return saved


class SetStatus:
    """Transition an item's status (open <-> bought, open <-> cancelled)."""

    def __init__(
        self,
        item_repo: ItemRepo,
        clock: Clock,
        event_bus: EventBus | None = None,
    ) -> None:
        self._item_repo = item_repo
        self._clock = clock
        self._event_bus = event_bus

    async def execute(
        self,
        *,
        household_id: str,
        item_id: str,
        member_id: str,
        status: ItemStatus,
    ) -> Item:
        item = await self._item_repo.get_by_id(household_id, item_id)
        if item is None:
            raise NotFoundError("Item not found")

        now = self._clock.now()
        transitioned = item.transition_to(status, actor_member_id=member_id, now=now)

        if transitioned.status == ItemStatus.OPEN:
            conflict = await self._item_repo.find_open_by_normalized_name(
                household_id, transitioned.name_normalized
            )
            if conflict is not None and conflict.id != transitioned.id:
                raise DuplicateItemError(
                    "Item already exists in the open list",
                    existing_item_id=conflict.id,
                )

        saved = await self._item_repo.update(transitioned)

        if self._event_bus is not None:
            await self._event_bus.publish(household_id, "item.updated", {"item_id": saved.id})

        return saved


class ListRecentBought:
    """Return the most-recent bought items for a household (history view)."""

    def __init__(self, item_repo: ItemRepo) -> None:
        self._item_repo = item_repo

    async def execute(self, *, household_id: str, limit: int = 50) -> list[Item]:
        return await self._item_repo.list_recent_bought(household_id, limit)


class ArchiveBought:
    """Soft-archive bought items older than N hours."""

    def __init__(
        self,
        item_repo: ItemRepo,
        clock: Clock,
        event_bus: EventBus | None = None,
    ) -> None:
        self._item_repo = item_repo
        self._clock = clock
        self._event_bus = event_bus

    async def execute(self, *, household_id: str, older_than_hours: int = 0) -> int:
        if older_than_hours < 0:
            raise ValidationError("older_than_hours must be non-negative")
        now = self._clock.now()
        cutoff = now - timedelta(hours=older_than_hours)
        count = await self._item_repo.archive_bought_before(household_id, cutoff, now)

        if count > 0 and self._event_bus is not None:
            await self._event_bus.publish(household_id, "item.updated", {"archived_count": count})

        return count
