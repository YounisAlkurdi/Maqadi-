"""Unit tests for PreviewPaste and ConfirmPaste use cases."""

from datetime import UTC, datetime

import pytest

from app.application.paste_import import ConfirmItemInput, ConfirmPaste, PreviewPaste
from app.domain.entities import Item, Member
from app.domain.enums import Category, ItemSource, ItemStatus, Urgency
from app.domain.errors import ValidationError
from app.domain.normalize import normalize_ar
from app.domain.ports import ExtractedItem, ExtractionResult
from tests.unit.fakes import FakeClock, FakeEventBus, FakeItemRepo, FakeMemberRepo


class FakeItemExtractor:
    def __init__(self, result: ExtractionResult) -> None:
        self._result = result
        self.last_text: str | None = None
        self.last_members: list[str] | None = None

    async def extract(self, text: str, known_members: list[str]) -> ExtractionResult:
        self.last_text = text
        self.last_members = known_members
        return self._result


def _make_member(
    household_id: str = "hh-1", member_id: str = "m-1", name: str = "أم يوسف"
) -> Member:
    return Member(
        id=member_id,
        household_id=household_id,
        display_name=name,
        color="#2B7A78",
        token_hash="hash",
        created_at=datetime(2026, 11, 27, 12, 0, tzinfo=UTC),
    )


def _make_open_item(
    household_id: str = "hh-1",
    item_id: str = "item-1",
    name: str = "لبن",
    qty: str | None = None,
) -> Item:
    now = datetime(2026, 11, 27, 12, 0, tzinfo=UTC)
    return Item(
        id=item_id,
        household_id=household_id,
        name=name,
        name_normalized=normalize_ar(name),
        quantity_text=qty,
        note=None,
        category=Category.DAIRY_EGGS,
        status=ItemStatus.OPEN,
        urgency=Urgency.NORMAL,
        requested_by_member_id="m-1",
        bought_by_member_id=None,
        source=ItemSource.MANUAL,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_preview_paste_annotates_merge_with_open_item() -> None:
    item_repo = FakeItemRepo()
    member_repo = FakeMemberRepo()
    await member_repo.create(_make_member())
    existing = _make_open_item(item_id="existing-1", name="لبن")
    await item_repo.create(existing)

    extractor = FakeItemExtractor(
        ExtractionResult(
            items=[
                ExtractedItem(
                    name="لبن",
                    quantity_text="2 لتر",
                    category=Category.DAIRY_EGGS,
                    urgency=Urgency.NORMAL,
                    requested_by="أم يوسف",
                    source_snippet="جيب لبن 2 لتر",
                    confidence=0.9,
                ),
                ExtractedItem(
                    name="خبز",
                    quantity_text=None,
                    category=Category.BAKERY,
                    urgency=Urgency.URGENT,
                    requested_by=None,
                    source_snippet="خبز ضروري",
                    confidence=0.8,
                ),
            ],
            ignored=["السلام عليكم"],
            engine="rules",
        )
    )

    use_case = PreviewPaste(extractor=extractor, item_repo=item_repo, member_repo=member_repo)
    res = await use_case.execute(household_id="hh-1", text="جيب لبن 2 لتر وخبز ضروري")

    assert res.engine == "rules"
    assert res.ignored == ["السلام عليكم"]
    assert len(res.items) == 2
    assert res.items[0].merge_with_item_id == "existing-1"
    assert res.items[1].merge_with_item_id is None
    assert extractor.last_members == ["أم يوسف"]


@pytest.mark.asyncio
async def test_preview_paste_rejects_empty_and_too_long() -> None:
    use_case = PreviewPaste(
        extractor=FakeItemExtractor(ExtractionResult(items=[], ignored=[], engine="rules")),
        item_repo=FakeItemRepo(),
        member_repo=FakeMemberRepo(),
        max_paste_chars=10,
    )

    with pytest.raises(ValidationError):
        await use_case.execute(household_id="hh-1", text="   ")

    with pytest.raises(ValidationError):
        await use_case.execute(household_id="hh-1", text="x" * 11)


@pytest.mark.asyncio
async def test_confirm_paste_creates_merges_and_skips_duplicates() -> None:
    item_repo = FakeItemRepo()
    member_repo = FakeMemberRepo()
    clock = FakeClock()
    bus = FakeEventBus()

    await member_repo.create(_make_member(member_id="m-1", name="أم يوسف"))
    await member_repo.create(_make_member(member_id="m-2", name="أبو يوسف"))
    existing = _make_open_item(item_id="existing-1", name="لبن", qty="1 لتر")
    await item_repo.create(existing)
    already_open = _make_open_item(item_id="existing-2", name="بيض")
    await item_repo.create(already_open)

    use_case = ConfirmPaste(
        item_repo=item_repo, member_repo=member_repo, clock=clock, event_bus=bus
    )
    saved = await use_case.execute(
        household_id="hh-1",
        current_member_id="m-1",
        items=[
            ConfirmItemInput(
                name="لبن",
                quantity_text="2 لتر",
                category=Category.DAIRY_EGGS,
                urgency=Urgency.URGENT,
                merge_with_item_id="existing-1",
            ),
            ConfirmItemInput(
                name="بيض",
                category=Category.DAIRY_EGGS,
            ),
            ConfirmItemInput(
                name="بندورة",
                quantity_text="2 كيلو",
                category=Category.PRODUCE,
                requested_by="أبو يوسف",
            ),
        ],
    )

    # 1 merged + 1 created; "بيض" skipped because it's already open
    assert len(saved) == 2
    merged = await item_repo.get_by_id("hh-1", "existing-1")
    assert merged is not None
    assert merged.urgency == Urgency.URGENT
    assert merged.note == "2 لتر"

    created = [i for i in saved if i.name == "بندورة"][0]
    assert created.source == ItemSource.PASTE
    assert created.requested_by_member_id == "m-2"
    assert len(bus.events) == 1
    assert bus.events[0][1] == "item.created"
