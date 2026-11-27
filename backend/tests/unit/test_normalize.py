"""Unit tests for Arabic text normalization."""

import pytest

from app.domain.normalize import normalize_ar


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("بندورة", "بندوره"),
        ("بَنْدُورَةٌ", "بندوره"),
        ("خـيـــار", "خيار"),
        ("أرز", "ارز"),
        ("إبريق شاي", "ابريق شاي"),
        ("آيس كريم", "ايس كريم"),
        ("مربى", "مربي"),
        ("طماطم طازجة", "طماطم طازجه"),
        ("٢ كيلو بطاطا", "2 كيلو بطاطا"),
        ("٣٥٠ غرام جبنة", "350 غرام جبنه"),
        ("  لبن   رايب  \n ", "لبن رايب"),
        ("Nescafe 3in1", "nescafe 3in1"),
        ("شامبو Head & Shoulders", "شامبو head & shoulders"),
        ("١٢٣٤٥٦٧٨٩٠", "1234567890"),
    ],
)
def test_normalize_ar(raw: str, expected: str) -> None:
    assert normalize_ar(raw) == expected
