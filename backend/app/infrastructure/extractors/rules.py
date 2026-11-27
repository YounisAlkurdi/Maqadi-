"""Rule-based fallback extractor (works with LLM_PROVIDER=none)."""

import re

from app.domain.enums import Urgency
from app.domain.normalize import normalize_ar
from app.domain.ports import ExtractedItem, ExtractionResult
from app.infrastructure.extractors.keywords_ar import classify_category

_SPEAKER_RE = re.compile(r"^([^:\n]{1,30}):\s*(.+)$")
_SPLIT_RE = re.compile(r"(?:\n|،|,|\s+و(?=\S))")

_LEADING_VERBS_RE = re.compile(
    r"^(?:يا\s+\S+\s+)?(?:لا\s+تنس[ىا]\s+)?(?:ت?جيب(?:وا)?|اشتري|بدي|بدنا|محتاجين|ناقصنا|هات|كمان)\s+"
)
_URGENT_WORDS = ("ضروري", "اليوم", "هلأ", "هلا", "مستعجل")
_NOISE_HINTS = (
    "السلام عليكم",
    "مرحبا",
    "صباح الخير",
    "مساء الخير",
    "يعطيك العافية",
    "يسلمو",
    "شكرا",
    "خلص جبناه",
    "مش لازم",
    "ما بدنا",
    "لا خلص",
    "مين أكل",
    "مين اكل",
    "متى",
    "وينك",
)
_QUANTITY_RE = re.compile(
    r"(\d+\s*(?:كيلو|كغم|غرام|جم|لتر|مل|علب[ةه]?|حبة|حبات|ربطة|ربطات|كيس|اكياس|طبقة|رغيف|أرغفة)?|"
    r"(?:نص|نصف|ربع|كيلو\s+ونص|كيلو|علب[ةه]|علبتين|حبة|حبتين|ربطة|ربطتين|طبقة|خبزتين))"
)


class RuleBasedExtractor:
    """Deterministic Arabic rule-based extractor used when AI is disabled or fails."""

    async def extract(self, text: str, known_members: list[str]) -> ExtractionResult:
        items: list[ExtractedItem] = []
        ignored: list[str] = []
        seen_names: set[str] = set()

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            requested_by: str | None = None
            speaker_match = _SPEAKER_RE.match(line)
            if speaker_match:
                speaker = speaker_match.group(1).strip()
                line = speaker_match.group(2).strip()
                if speaker in known_members:
                    requested_by = speaker

            if self._is_noise(line):
                ignored.append(raw_line.strip())
                continue

            urgency = Urgency.URGENT if any(w in line for w in _URGENT_WORDS) else Urgency.NORMAL

            for part in _SPLIT_RE.split(line):
                fragment = part.strip()
                if not fragment or self._is_noise(fragment):
                    continue

                cleaned = _LEADING_VERBS_RE.sub("", fragment).strip()
                cleaned = _LEADING_VERBS_RE.sub("", cleaned).strip()
                if not cleaned or len(cleaned) < 2:
                    continue

                qty_match = _QUANTITY_RE.search(cleaned)
                quantity_text: str | None = None
                name = cleaned
                if qty_match:
                    qty = qty_match.group(0).strip()
                    if qty == "خبزتين":
                        quantity_text = "خبزتين"
                        name = "خبز"
                    else:
                        quantity_text = qty
                        remainder = (
                            cleaned[: qty_match.start()] + " " + cleaned[qty_match.end() :]
                        ).strip()
                        if remainder:
                            name = remainder

                norm = normalize_ar(name)
                if not norm or norm in seen_names:
                    continue
                seen_names.add(norm)

                items.append(
                    ExtractedItem(
                        name=name,
                        quantity_text=quantity_text,
                        category=classify_category(norm),
                        urgency=urgency,
                        requested_by=requested_by,
                        source_snippet=fragment,
                        confidence=0.6,
                    )
                )

        return ExtractionResult(items=items, ignored=ignored, engine="rules")

    def _is_noise(self, text: str) -> bool:
        if "؟" in text or "?" in text:
            return True
        if any(hint in text for hint in _NOISE_HINTS):
            return True
        # Emoji-only or punctuation-only
        return not any(ch.isalnum() for ch in text)
