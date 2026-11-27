"""Unit tests verifying LLM API keys are sent via headers and redacted from errors."""

import httpx
import pytest

from app.infrastructure.extractors.llm import LLMItemExtractor


async def test_gemini_uses_header_and_redacts_key_on_error() -> None:
    secret_key = "SECRET_TEST_KEY_999"
    captured_headers: dict[str, str] = {}
    captured_url = ""

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_headers, captured_url
        captured_headers = dict(request.headers)
        captured_url = str(request.url)
        return httpx.Response(
            404,
            request=request,
            text=f"Error with key {secret_key}",
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        extractor = LLMItemExtractor(
            provider="gemini",
            api_key=secret_key,
            model="gemini-3-flash-preview",
            http_client=client,
        )
        with pytest.raises(RuntimeError) as exc_info:
            await extractor.extract("بندورة", [])

    assert secret_key not in captured_url
    assert captured_headers.get("x-goog-api-key") == secret_key
    assert secret_key not in str(exc_info.value)
