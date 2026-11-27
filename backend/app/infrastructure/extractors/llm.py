"""LLM-based item extractor supporting Anthropic and Gemini via httpx."""

import json
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.domain.enums import Category, Urgency
from app.domain.ports import ExtractedItem, ExtractionResult
from app.infrastructure.extractors.prompts import SYSTEM_PROMPT


class _LLMItemSchema(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    quantity_text: str | None = None
    category: Category = Category.OTHER
    urgency: Urgency = Urgency.NORMAL
    requested_by: str | None = None
    source_snippet: str = ""
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class _LLMResponseSchema(BaseModel):
    items: list[_LLMItemSchema] = Field(default_factory=list)
    ignored: list[str] = Field(default_factory=list)


class LLMItemExtractor:
    """Calls configured LLM provider with strict JSON validation and 1 retry."""

    def __init__(
        self,
        *,
        provider: str,
        api_key: str,
        model: str,
        timeout_seconds: int = 12,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._provider = provider.lower().strip()
        self._api_key = api_key
        self._model = model
        self._timeout = timeout_seconds
        self._http_client = http_client

    async def extract(self, text: str, known_members: list[str]) -> ExtractionResult:
        if self._provider == "none" or not self._api_key:
            raise RuntimeError("LLM provider is not configured")

        user_prompt = f"KNOWN_MEMBERS: {json.dumps(known_members, ensure_ascii=False)}\n\n{text}"

        last_exc: Exception | None = None
        for _ in range(2):
            try:
                raw_json = await self._call_provider(user_prompt)
                parsed = _LLMResponseSchema.model_validate(json.loads(raw_json))
                return ExtractionResult(
                    items=[
                        ExtractedItem(
                            name=i.name.strip(),
                            quantity_text=i.quantity_text.strip() if i.quantity_text else None,
                            category=i.category,
                            urgency=i.urgency,
                            requested_by=i.requested_by
                            if i.requested_by in known_members
                            else None,
                            source_snippet=i.source_snippet,
                            confidence=i.confidence,
                        )
                        for i in parsed.items
                    ],
                    ignored=parsed.ignored,
                    engine="llm",
                )
            except (
                httpx.HTTPError,
                json.JSONDecodeError,
                ValidationError,
                KeyError,
                ValueError,
            ) as exc:
                last_exc = exc

        raise RuntimeError(f"LLM extraction failed after retry: {last_exc}") from last_exc

    async def _call_provider(self, user_prompt: str) -> str:
        if self._http_client is not None:
            return await self._dispatch(self._http_client, user_prompt)
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            return await self._dispatch(client, user_prompt)

    async def _dispatch(self, client: httpx.AsyncClient, user_prompt: str) -> str:
        if self._provider == "anthropic":
            model = self._model or "claude-3-5-haiku-latest"
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 1024,
                    "temperature": 0.1,
                    "system": SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            return str(data["content"][0]["text"])

        if self._provider == "gemini":
            model = self._model or "gemini-2.0-flash"
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": self._api_key},
                json={
                    "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                    "contents": [{"parts": [{"text": user_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.1,
                        "responseMimeType": "application/json",
                    },
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return str(data["candidates"][0]["content"]["parts"][0]["text"])

        raise ValueError(f"Unsupported LLM provider: {self._provider}")
