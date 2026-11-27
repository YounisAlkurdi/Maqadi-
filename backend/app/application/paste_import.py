"""Use cases for AI paste preview and confirmation (never persists raw text)."""

import uuid
from dataclasses import dataclass, replace
from typing import Literal

from app.domain.entities import Item
from app.domain.enums import Category, ItemSource, ItemStatus, Urgency
from app.domain.errors import ValidationError
from app.domain.normalize import normalize_ar
from app.domain.ports import Clock, EventBus, ItemExtractor, ItemRepo, MemberRepo


@dataclass(frozen=True)
class PreviewItem:
    name: str
    quantity_text: str | None
    category: Category
    urgency: Urgency
    requested_by: str | None
    source_snippet: str
    confidence: float
    merge_with_item_id: str | None


@dataclass(frozen=True)
class PreviewPasteResult:
    items: list[PreviewItem]
    ignored: list[str]
    engine: Literal["llm", "rules"]


@dataclass(frozen=True)
class ConfirmItemInput:
    name: str
    quantity_text: str | None = None
    category: Category = Category.OTHER
    urgency: Urgency = Urgency.NORMAL
    requested_by: str | None = None
    merge_with_item_id: str | None = None


class PreviewPaste:
    """Extract structured items from pasted text and annotate open-item merge candidates."""

    def __init__(
        self,
        extractor: ItemExtractor,
        item_repo: ItemRepo,
        member_repo: MemberRepo,
        *,
        max_paste_chars: int = 6000,
    ) -> None:
        self._extractor = extractor
        self._item_repo = item_repo
        self._member_repo = member_repo
        self._max_paste_chars = max_paste_chars

    async def execute(self, *, household_id: str, text: str) -> PreviewPasteResult:
        if len(text) > self._max_paste_chars:
            raise ValidationError(
                f"Pasted text exceeds maximum length of {self._max_paste_chars} characters"
            )
        if not text.strip():
            raise ValidationError("Pasted text cannot be empty")

        members = await self._member_repo.list_by_household(household_id)
        known_names = [m.display_name for m in members]

        extraction = await self._extractor.extract(text, known_names)

        open_items = await self._item_repo.list_by_household(
            household_id, status=ItemStatus.OPEN, include_archived=False
        )
        open_by_norm = {item.name_normalized: item.id for item in open_items}

        preview_items: list[PreviewItem] = []
        for ext in extraction.items:
            norm = normalize_ar(ext.name)
            merge_id = open_by_norm.get(norm)
            preview_items.append(
                PreviewItem(
                    name=ext.name,
                    quantity_text=ext.quantity_text,
                    category=ext.category,
                    urgency=ext.urgency,
                    requested_by=ext.requested_by,
                    source_snippet=ext.source_snippet,
                    confidence=ext.confidence,
                    merge_with_item_id=merge_id,
                )
            )

        return PreviewPasteResult(
            items=preview_items,
            ignored=extraction.ignored,
            engine=extraction.engine,
        )


class ConfirmPaste:
    """Persist user-confirmed items from paste preview, applying dedupe/merge rules."""

    def __init__(
        self,
        item_repo: ItemRepo,
        member_repo: MemberRepo,
        clock: Clock,
        event_bus: EventBus | None = None,
    ) -> None:
        self._item_repo = item_repo
        self._member_repo = member_repo
        self._clock = clock
        self._event_bus = event_bus

    async def execute(
        self,
        *,
        household_id: str,
        current_member_id: str,
        items: list[ConfirmItemInput],
    ) -> list[Item]:
        members = await self._member_repo.list_by_household(household_id)
        member_id_by_name = {m.display_name: m.id for m in members}
        now = self._clock.now()
        saved: list[Item] = []

        for entry in items:
            clean_name = entry.name.strip()
            if not clean_name:
                continue
            norm = normalize_ar(clean_name)
            if not norm:
                continue

            qty = (
                entry.quantity_text.strip()
                if entry.quantity_text and entry.quantity_text.strip()
                else None
            )
            requester_id = (
                member_id_by_name.get(entry.requested_by, current_member_id)
                if entry.requested_by
                else current_member_id
            )

            if entry.merge_with_item_id:
                existing = await self._item_repo.get_by_id(household_id, entry.merge_with_item_id)
                if existing is not None and existing.status == ItemStatus.OPEN:
                    merged_note = existing.note
                    if qty and qty != existing.quantity_text:
                        merged_note = f"{existing.note} | {qty}" if existing.note else qty
                    updated = replace(
                        existing,
                        note=merged_note,
                        urgency=Urgency.URGENT
                        if entry.urgency == Urgency.URGENT
                        else existing.urgency,
                        updated_at=now,
                    )
                    saved.append(await self._item_repo.update(updated))
                    continue

            existing_open = await self._item_repo.find_open_by_normalized_name(household_id, norm)
            if existing_open is not None:
                continue

            new_item = Item(
                id=str(uuid.uuid4()),
                household_id=household_id,
                name=clean_name,
                name_normalized=norm,
                quantity_text=qty,
                note=None,
                category=entry.category,
                status=ItemStatus.OPEN,
                urgency=entry.urgency,
                requested_by_member_id=requester_id,
                bought_by_member_id=None,
                source=ItemSource.PASTE,
                created_at=now,
                updated_at=now,
            )
            saved.append(await self._item_repo.create(new_item))

        if saved and self._event_bus is not None:
            await self._event_bus.publish(household_id, "item.created", {"count": len(saved)})

        return saved
