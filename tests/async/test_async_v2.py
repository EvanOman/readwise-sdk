"""Tests for async Readwise API v2 client."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from readwise_sdk import AsyncReadwiseClient
from readwise_sdk.client import READWISE_API_V2_BASE
from readwise_sdk.exceptions import NotFoundError
from readwise_sdk.v2.models import BookCategory, HighlightCreate, HighlightUpdate


class TestAsyncV2Highlights:
    """Tests for async highlight operations."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_highlights(self, api_key: str) -> None:
        """Test listing highlights asynchronously."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": 1, "text": "First highlight"},
                        {"id": 2, "text": "Second highlight"},
                    ],
                    "next": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            highlights = [h async for h in client.v2.list_highlights()]

            assert len(highlights) == 2
            assert highlights[0].id == 1
            assert highlights[0].text == "First highlight"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_highlights_with_filters(self, api_key: str) -> None:
        """Test listing highlights with filters."""
        route = respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "next": None},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            _ = [h async for h in client.v2.list_highlights(book_id=123, page_size=50)]

            assert route.called
            request = route.calls.last.request
            assert "book_id=123" in str(request.url)
            assert "page_size=50" in str(request.url)

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_highlights_with_date_filters(self, api_key: str) -> None:
        """Test listing highlights with highlighted_after and highlighted_before filters."""
        route = respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "next": None},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            after = datetime(2024, 1, 1, tzinfo=UTC)
            before = datetime(2024, 6, 30, tzinfo=UTC)
            _ = [
                h
                async for h in client.v2.list_highlights(
                    highlighted_after=after,
                    highlighted_before=before,
                )
            ]

            assert route.called
            request = route.calls.last.request
            url_str = str(request.url)
            assert "highlighted_at__gt=" in url_str
            assert "highlighted_at__lt=" in url_str

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_highlight(self, api_key: str) -> None:
        """Test getting a single highlight."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/123/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 123,
                    "text": "Test highlight",
                    "note": "My note",
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            highlight = await client.v2.get_highlight(123)

            assert highlight.id == 123
            assert highlight.text == "Test highlight"
            assert highlight.note == "My note"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_highlight_not_found(self, api_key: str) -> None:
        """Test getting a non-existent highlight."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/99999/").mock(
            return_value=httpx.Response(404, text="Not found")
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            with pytest.raises(NotFoundError):
                await client.v2.get_highlight(99999)

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_highlights(self, api_key: str) -> None:
        """Test creating highlights."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [101, 102]}],
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            highlights = [
                HighlightCreate(text="First new highlight", title="Book 1"),
                HighlightCreate(text="Second new highlight", title="Book 2"),
            ]
            result = await client.v2.create_highlights(highlights)

            assert result == [101, 102]

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_highlight(self, api_key: str) -> None:
        """Test updating a highlight."""
        respx.patch(f"{READWISE_API_V2_BASE}/highlights/123/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 123,
                    "text": "Original text",
                    "note": "Updated note",
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            update = HighlightUpdate(note="Updated note")
            highlight = await client.v2.update_highlight(123, update)

            assert highlight.id == 123
            assert highlight.note == "Updated note"

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_highlight(self, api_key: str) -> None:
        """Test deleting a highlight."""
        respx.delete(f"{READWISE_API_V2_BASE}/highlights/123/").mock(
            return_value=httpx.Response(204)
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            await client.v2.delete_highlight(123)  # Should not raise


class TestAsyncV2Books:
    """Tests for async book operations."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_books(self, api_key: str) -> None:
        """Test listing books."""
        respx.get(f"{READWISE_API_V2_BASE}/books/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": 1, "title": "Book One", "author": "Author One"},
                        {"id": 2, "title": "Book Two", "author": "Author Two"},
                    ],
                    "next": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            books = [book async for book in client.v2.list_books()]

            assert len(books) == 2
            assert books[0].title == "Book One"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_books_by_category(self, api_key: str) -> None:
        """Test listing books filtered by category."""
        route = respx.get(f"{READWISE_API_V2_BASE}/books/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "next": None},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            _ = [book async for book in client.v2.list_books(category=BookCategory.ARTICLES)]

            assert route.called
            request = route.calls.last.request
            assert "category=articles" in str(request.url)

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_books_with_filters(self, api_key: str) -> None:
        """Test listing books with source, updated_before, last_highlight_after/before."""
        route = respx.get(f"{READWISE_API_V2_BASE}/books/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "next": None},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            updated_before = datetime(2024, 12, 31, tzinfo=UTC)
            highlight_after = datetime(2024, 1, 1, tzinfo=UTC)
            highlight_before = datetime(2024, 6, 30, tzinfo=UTC)
            _ = [
                book
                async for book in client.v2.list_books(
                    source="kindle",
                    updated_before=updated_before,
                    last_highlight_after=highlight_after,
                    last_highlight_before=highlight_before,
                )
            ]

            assert route.called
            request = route.calls.last.request
            url_str = str(request.url)
            assert "source=kindle" in url_str
            assert "updated__lt=" in url_str
            assert "last_highlight_at__gt=" in url_str
            assert "last_highlight_at__lt=" in url_str

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_book(self, api_key: str) -> None:
        """Test getting a single book."""
        respx.get(f"{READWISE_API_V2_BASE}/books/456/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": 456,
                    "title": "Test Book",
                    "author": "Test Author",
                    "num_highlights": 10,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            book = await client.v2.get_book(456)

            assert book.id == 456
            assert book.title == "Test Book"
            assert book.num_highlights == 10


class TestAsyncV2HighlightTags:
    """Tests for async highlight tag operations."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_highlight_tags(self, api_key: str) -> None:
        """Test listing tags for a highlight."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/123/tags/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": 1, "name": "favorite"},
                        {"id": 2, "name": "important"},
                    ],
                    "next": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            tags = [tag async for tag in client.v2.list_highlight_tags(123)]

            assert len(tags) == 2
            assert tags[0].name == "favorite"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_highlight_tag(self, api_key: str) -> None:
        """Test adding a tag to a highlight."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/123/tags/").mock(
            return_value=httpx.Response(
                200,
                json={"id": 5, "name": "new-tag"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            tag = await client.v2.create_highlight_tag(123, "new-tag")

            assert tag.id == 5
            assert tag.name == "new-tag"

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_highlight_tag(self, api_key: str) -> None:
        """Test updating a tag on a highlight."""
        respx.patch(f"{READWISE_API_V2_BASE}/highlights/123/tags/5/").mock(
            return_value=httpx.Response(
                200,
                json={"id": 5, "name": "updated-tag"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            tag = await client.v2.update_highlight_tag(123, 5, "updated-tag")

            assert tag.id == 5
            assert tag.name == "updated-tag"

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_highlight_tag(self, api_key: str) -> None:
        """Test removing a tag from a highlight."""
        respx.delete(f"{READWISE_API_V2_BASE}/highlights/123/tags/5/").mock(
            return_value=httpx.Response(204)
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            await client.v2.delete_highlight_tag(123, 5)  # Should not raise


class TestAsyncV2BookTags:
    """Tests for async book tag operations."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_book_tags(self, api_key: str) -> None:
        """Test listing tags for a book."""
        respx.get(f"{READWISE_API_V2_BASE}/books/456/tags/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [{"id": 1, "name": "tech"}],
                    "next": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            tags = [tag async for tag in client.v2.list_book_tags(456)]

            assert len(tags) == 1
            assert tags[0].name == "tech"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_book_tag(self, api_key: str) -> None:
        """Test adding a tag to a book."""
        respx.post(f"{READWISE_API_V2_BASE}/books/456/tags/").mock(
            return_value=httpx.Response(
                200,
                json={"id": 10, "name": "programming"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            tag = await client.v2.create_book_tag(456, "programming")

            assert tag.id == 10
            assert tag.name == "programming"

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_book_tag(self, api_key: str) -> None:
        """Test updating a tag on a book."""
        respx.patch(f"{READWISE_API_V2_BASE}/books/456/tags/10/").mock(
            return_value=httpx.Response(
                200,
                json={"id": 10, "name": "python"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            tag = await client.v2.update_book_tag(456, 10, "python")

            assert tag.id == 10
            assert tag.name == "python"

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_book_tag(self, api_key: str) -> None:
        """Test removing a tag from a book."""
        respx.delete(f"{READWISE_API_V2_BASE}/books/456/tags/10/").mock(
            return_value=httpx.Response(204)
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            await client.v2.delete_book_tag(456, 10)  # Should not raise


class TestAsyncV2Export:
    """Tests for async export operations."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_export_highlights(self, api_key: str) -> None:
        """Test exporting highlights."""
        respx.get(url__startswith=f"{READWISE_API_V2_BASE}/export/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "user_book_id": 1,
                            "title": "Book One",
                            "author": "Author One",
                            "highlights": [
                                {"id": 1, "text": "Highlight 1"},
                                {"id": 2, "text": "Highlight 2"},
                            ],
                        }
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            export_books = [book async for book in client.v2.export_highlights()]

            assert len(export_books) == 1
            assert export_books[0].title == "Book One"
            assert len(export_books[0].highlights) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_export_with_filters(self, api_key: str) -> None:
        """Test exporting highlights with updated_after, book_ids, and include_deleted."""
        route = respx.get(url__startswith=f"{READWISE_API_V2_BASE}/export/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "user_book_id": 1,
                            "title": "Filtered Book",
                            "author": "Author",
                            "highlights": [{"id": 10, "text": "Filtered highlight"}],
                        }
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            updated_after = datetime(2024, 1, 1, tzinfo=UTC)
            export_books = [
                book
                async for book in client.v2.export_highlights(
                    updated_after=updated_after,
                    book_ids=[1, 2, 3],
                    include_deleted=True,
                )
            ]

            assert route.called
            request = route.calls.last.request
            url_str = str(request.url)
            assert "updatedAfter=" in url_str
            assert "ids=1%2C2%2C3" in url_str or "ids=1,2,3" in url_str
            assert "includeDeleted=true" in url_str
            assert len(export_books) == 1
            assert export_books[0].title == "Filtered Book"


class TestAsyncV2DailyReview:
    """Tests for async daily review operations."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_daily_review(self, api_key: str) -> None:
        """Test getting daily review."""
        respx.get(f"{READWISE_API_V2_BASE}/review/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "review_id": 12345,
                    "review_url": "https://readwise.io/review/12345",
                    "review_completed": False,
                    "highlights": [
                        {"id": 1, "text": "Review highlight 1"},
                        {"id": 2, "text": "Review highlight 2"},
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            review = await client.v2.get_daily_review()

            assert review.review_id == 12345
            assert len(review.highlights) == 2
            assert review.review_completed is False
