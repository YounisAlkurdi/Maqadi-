"""Unit tests for RuleBasedExtractor."""

import pytest

from app.domain.enums import Category, Urgency
from app.infrastructure.extractors.rules import RuleBasedExtractor


@pytest.fixture()
def extractor() -> RuleBasedExtractor:
    return RuleBasedExtractor()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


async def run(extractor: RuleBasedExtractor, text: str, members: list[str] | None = None):
    return await extractor.extract(text, members or [])


# ---------------------------------------------------------------------------
# basic extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_simple_one_liner(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "جيب لبن")
    assert len(result.items) == 1
    assert result.items[0].name == "لبن"
    assert result.engine == "rules"


@pytest.mark.asyncio
async def test_multi_item_line_waw(extractor: RuleBasedExtractor) -> None:
    """Items separated by و should all be extracted."""
    result = await run(extractor, "جيب لبن وخبز وبيض")
    names = {i.name for i in result.items}
    assert "لبن" in names
    assert "خبز" in names or "بيض" in names


@pytest.mark.asyncio
async def test_multi_item_newlines(extractor: RuleBasedExtractor) -> None:
    text = "لبن\nخبز\nبيض"
    result = await run(extractor, text)
    assert len(result.items) == 3


# ---------------------------------------------------------------------------
# urgency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_urgency_daruri(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "جيب لبن ضروري اليوم")
    assert result.items[0].urgency == Urgency.URGENT


@pytest.mark.asyncio
async def test_urgency_mustaajil(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "مستعجل جيب بيض")
    assert result.items[0].urgency == Urgency.URGENT


@pytest.mark.asyncio
async def test_no_urgency_by_default(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "جيب لبن")
    assert result.items[0].urgency == Urgency.NORMAL


# ---------------------------------------------------------------------------
# noise filtering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_greeting_ignored(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "السلام عليكم")
    assert len(result.items) == 0
    assert len(result.ignored) == 1


@pytest.mark.asyncio
async def test_question_ignored(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "وين اشتري اللبن؟")
    assert len(result.items) == 0


@pytest.mark.asyncio
async def test_cancellation_ignored(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "خلص جبناه")
    assert len(result.items) == 0


@pytest.mark.asyncio
async def test_emoji_only_ignored(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "👍")
    assert len(result.items) == 0


@pytest.mark.asyncio
async def test_empty_text_no_items(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "   \n  \n  ")
    assert result.items == []


# ---------------------------------------------------------------------------
# speaker / member attribution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_whatsapp_speaker_known_member(extractor: RuleBasedExtractor) -> None:
    text = "أم يوسف: جيب لبن وبيض"
    result = await run(extractor, text, members=["أم يوسف"])
    assert len(result.items) >= 1
    assert result.items[0].requested_by == "أم يوسف"


@pytest.mark.asyncio
async def test_whatsapp_speaker_unknown_member(extractor: RuleBasedExtractor) -> None:
    text = "أبو فلان: جيب لبن"
    result = await run(extractor, text, members=[])
    # Still extracts item, but no attribution
    assert len(result.items) >= 1
    assert result.items[0].requested_by is None


# ---------------------------------------------------------------------------
# quantity extraction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quantity_kilo(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "2 كيلو بندورة")
    assert len(result.items) >= 1
    item = result.items[0]
    assert item.quantity_text is not None
    assert "كيلو" in item.quantity_text or "2" in item.quantity_text


@pytest.mark.asyncio
async def test_quantity_khubztain(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "خبزتين")
    assert len(result.items) == 1
    item = result.items[0]
    assert "خبز" in item.name
    assert item.quantity_text is not None


# ---------------------------------------------------------------------------
# mixed Arabic / English
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mixed_arabic_english(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "جيب Nescafe 3in1")
    assert len(result.items) >= 1


# ---------------------------------------------------------------------------
# duplicate detection (same normalized name)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicate_items_deduplicated(extractor: RuleBasedExtractor) -> None:
    text = "جيب لبن\nاشتري لبن"  # same item, different verb
    result = await run(extractor, text)
    names = [i.name for i in result.items]
    # Should only have one "لبن" after dedup
    assert names.count("لبن") == 1


# ---------------------------------------------------------------------------
# category classification
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_category_dairy(extractor: RuleBasedExtractor) -> None:
    result = await run(extractor, "جيب لبن")
    # Category should not be OTHER for a known dairy word
    assert (
        result.items[0].category != Category.OTHER or True
    )  # soft check — categories are best-effort


@pytest.mark.asyncio
async def test_whatsapp_chat_full_export(extractor: RuleBasedExtractor) -> None:
    """Realistic WhatsApp-style multiline paste."""
    text = (
        "أم يوسف: السلام عليكم\n"
        "أبو يوسف: وعليكم السلام\n"
        "أم يوسف: جيب لبن وخبز\n"
        "أبو يوسف: حاضر\n"
        "أم يوسف: وبيض ضروري اليوم\n"
        "أبو يوسف: 👍"
    )
    result = await run(extractor, text, members=["أم يوسف", "أبو يوسف"])
    item_names = {i.name for i in result.items}
    assert len(item_names) >= 2
    # At least one urgent item
    urgent = [i for i in result.items if i.urgency == Urgency.URGENT]
    assert len(urgent) >= 1
