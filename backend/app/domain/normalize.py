"""Pure Arabic text normalization for deduplication and matching."""

import re

_TASHKEEL_RE = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_TATWEEL = "\u0640"
_WHITESPACE_RE = re.compile(r"\s+")

_CHAR_TRANSLATION = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ة": "ه",
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
        "۰": "0",
        "۱": "1",
        "۲": "2",
        "۳": "3",
        "۴": "4",
        "۵": "5",
        "۶": "6",
        "۷": "7",
        "۸": "8",
        "۹": "9",
        _TATWEEL: "",
    }
)


def normalize_ar(text: str) -> str:
    """Normalize Arabic text for deduplication and search matching.

    Strips tashkeel and tatweel, unifies alef/ya/ta-marbuta variants,
    converts Arabic-Indic digits to ASCII, lowercases Latin text,
    and collapses whitespace.
    """
    cleaned = _TASHKEEL_RE.sub("", text)
    cleaned = cleaned.translate(_CHAR_TRANSLATION)
    cleaned = cleaned.lower()
    return _WHITESPACE_RE.sub(" ", cleaned).strip()
