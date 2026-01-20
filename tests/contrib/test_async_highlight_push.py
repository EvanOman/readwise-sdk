"""Tests for AsyncHighlightPusher."""

import httpx
import pytest
import respx

from readwise_sdk import AsyncReadwiseClient
from readwise_sdk.client import READWISE_API_V2_BASE
from readwise_sdk.contrib.highlight_push import (
    MAX_TEXT_LENGTH,
    AsyncHighlightPusher,
    SimpleHighlight,
)
from readwise_sdk.v2.models import BookCategory


class TestAsyncHighlightPusher:
    """Tests for AsyncHighlightPusher."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_push_single_highlight(self, api_key: str) -> None:
        """Test pushing a single highlight."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [123]}],
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            pusher = AsyncHighlightPusher(client)
            result = await pusher.push(text="Test text", title="Test Title")

        assert result.success is True
        assert result.highlight_id == 123
        assert result.was_truncated is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_push_with_all_fields(self, api_key: str) -> None:
        """Test pushing a highlight with all fields."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [456]}],
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            pusher = AsyncHighlightPusher(client)
            result = await pusher.push(
                text="Full text",
                title="Full Title",
                author="John Doe",
                source_url="https://example.com",
                category=BookCategory.BOOKS,
                note="My note",
            )

        assert result.success is True
        assert result.highlight_id == 456

    @pytest.mark.asyncio
    @respx.mock
    async def test_push_highlight_object(self, api_key: str) -> None:
        """Test pushing a SimpleHighlight object."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [789]}],
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            pusher = AsyncHighlightPusher(client)
            highlight = SimpleHighlight(text="Highlight text", title="Title")
            result = await pusher.push_highlight(highlight)

        assert result.success is True
        assert result.highlight_id == 789
        assert result.original == highlight

    @pytest.mark.asyncio
    @respx.mock
    async def test_push_batch(self, api_key: str) -> None:
        """Test pushing multiple highlights."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [1, 2, 3]}],
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            pusher = AsyncHighlightPusher(client)
            highlights = [
                SimpleHighlight(text="First", title="Title 1"),
                SimpleHighlight(text="Second", title="Title 2"),
                SimpleHighlight(text="Third", title="Title 3"),
            ]
            results = await pusher.push_batch(highlights)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert [r.highlight_id for r in results] == [1, 2, 3]

    @pytest.mark.asyncio
    @respx.mock
    async def test_push_batch_empty(self, api_key: str) -> None:
        """Test pushing empty list."""
        async with AsyncReadwiseClient(api_key=api_key) as client:
            pusher = AsyncHighlightPusher(client)
            results = await pusher.push_batch([])

        assert results == []

    @pytest.mark.asyncio
    @respx.mock
    async def test_push_batch_api_failure(self, api_key: str) -> None:
        """Test handling API failure for batch push."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            pusher = AsyncHighlightPusher(client)
            highlights = [SimpleHighlight(text="Test", title="Title")]
            results = await pusher.push_batch(highlights)

        assert len(results) == 1
        assert results[0].success is False
        assert results[0].error is not None

    @pytest.mark.asyncio
    @respx.mock
    async def test_push_with_truncation(self, api_key: str) -> None:
        """Test automatic field truncation."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(200, json=[{"modified_highlights": [100]}])
        )

        long_text = "x" * (MAX_TEXT_LENGTH + 100)

        async with AsyncReadwiseClient(api_key=api_key) as client:
            pusher = AsyncHighlightPusher(client)
            result = await pusher.push(text=long_text, title="Title")

        assert result.success is True
        assert result.was_truncated is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_push_no_truncation_when_disabled(self, api_key: str) -> None:
        """Test that truncation is not applied when disabled."""
        route = respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(200, json=[{"modified_highlights": [100]}])
        )

        # Text within limits - should not truncate
        short_text = "Short text"

        async with AsyncReadwiseClient(api_key=api_key) as client:
            pusher = AsyncHighlightPusher(client, auto_truncate=False)
            result = await pusher.push(text=short_text, title="Title")

        assert result.success is True
        assert result.was_truncated is False
        assert route.called

    @pytest.mark.asyncio
    @respx.mock
    async def test_validate_token(self, api_key: str) -> None:
        """Test token validation."""
        respx.get(f"{READWISE_API_V2_BASE}/auth/").mock(return_value=httpx.Response(204))

        async with AsyncReadwiseClient(api_key=api_key) as client:
            pusher = AsyncHighlightPusher(client)
            result = await pusher.validate_token()

        assert result is True
