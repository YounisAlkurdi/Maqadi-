"""Chain extractor: tries LLM first, falls back to RuleBasedExtractor."""

from app.domain.ports import ExtractionResult, ItemExtractor


class ChainExtractor:
    """Tries primary extractor (LLM) and falls back to rules on any failure."""

    def __init__(self, primary: ItemExtractor | None, fallback: ItemExtractor) -> None:
        self._primary = primary
        self._fallback = fallback

    async def extract(self, text: str, known_members: list[str]) -> ExtractionResult:
        if self._primary is not None:
            try:
                return await self._primary.extract(text, known_members)
            except Exception:
                pass
        return await self._fallback.extract(text, known_members)
