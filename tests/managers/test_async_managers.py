"""Tests for async manager classes."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from readwise_sdk import AsyncReadwiseClient
from readwise_sdk.client import READWISE_API_V2_BASE, READWISE_API_V3_BASE
from readwise_sdk.managers import (
    AsyncBookManager,
    AsyncDocumentManager,
    AsyncHighlightManager,
    AsyncSyncManager,
)
from readwise_sdk.v2.models import BookCategory


class TestAsyncHighlightManager:
    """Tests for AsyncHighlightManager."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_all_highlights(self, api_key: str) -> None:
        """Test getting all highlights."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [
                        {"id": 1, "text": "First"},
                        {"id": 2, "text": "Second"},
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncHighlightManager(client)
            highlights = await manager.get_all_highlights()

        assert len(highlights) == 2
        assert highlights[0].id == 1
        assert highlights[1].id == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_highlights_since_days(self, api_key: str) -> None:
        """Test getting highlights since N days ago."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [{"id": 1, "text": "Recent"}],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncHighlightManager(client)
            highlights = await manager.get_highlights_since(days=7)

        assert len(highlights) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_highlights_by_book(self, api_key: str) -> None:
        """Test getting highlights by book ID."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [{"id": 1, "text": "Book highlight", "book_id": 42}],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncHighlightManager(client)
            highlights = await manager.get_highlights_by_book(42)

        assert len(highlights) == 1
        assert highlights[0].book_id == 42

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_highlights(self, api_key: str) -> None:
        """Test searching highlights."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [
                        {"id": 1, "text": "Python is great"},
                        {"id": 2, "text": "JavaScript too"},
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncHighlightManager(client)
            results = await manager.search_highlights("python")

        assert len(results) == 1
        assert "Python" in results[0].text

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_highlight(self, api_key: str) -> None:
        """Test creating a highlight."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(200, json=[{"modified_highlights": [999]}])
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncHighlightManager(client)
            highlight_id = await manager.create_highlight(
                text="New highlight",
                title="Test Book",
            )

        assert highlight_id == 999

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_highlight_count(self, api_key: str) -> None:
        """Test getting highlight count."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [
                        {"id": 1, "text": "One"},
                        {"id": 2, "text": "Two"},
                        {"id": 3, "text": "Three"},
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncHighlightManager(client)
            count = await manager.get_highlight_count()

        assert count == 3


class TestAsyncBookManager:
    """Tests for AsyncBookManager."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_all_books(self, api_key: str) -> None:
        """Test getting all books."""
        respx.get(f"{READWISE_API_V2_BASE}/books/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [
                        {"id": 1, "title": "Book 1", "num_highlights": 5},
                        {"id": 2, "title": "Book 2", "num_highlights": 3},
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncBookManager(client)
            books = await manager.get_all_books()

        assert len(books) == 2
        assert books[0].title == "Book 1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_books_by_category(self, api_key: str) -> None:
        """Test getting books by category."""
        respx.get(f"{READWISE_API_V2_BASE}/books/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [
                        {"id": 1, "title": "Article", "category": "articles", "num_highlights": 2}
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncBookManager(client)
            books = await manager.get_books_by_category(BookCategory.ARTICLES)

        assert len(books) == 1
        assert books[0].category == BookCategory.ARTICLES

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_book_with_highlights(self, api_key: str) -> None:
        """Test getting a book with its highlights."""
        respx.get(f"{READWISE_API_V2_BASE}/books/1/").mock(
            return_value=httpx.Response(
                200,
                json={"id": 1, "title": "Test Book", "num_highlights": 2},
            )
        )
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [
                        {"id": 1, "text": "Highlight 1", "book_id": 1},
                        {"id": 2, "text": "Highlight 2", "book_id": 1},
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncBookManager(client)
            result = await manager.get_book_with_highlights(1)

        assert result.book.id == 1
        assert len(result.highlights) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_books(self, api_key: str) -> None:
        """Test searching books."""
        respx.get(f"{READWISE_API_V2_BASE}/books/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [
                        {"id": 1, "title": "Python Guide", "num_highlights": 5},
                        {"id": 2, "title": "JavaScript Guide", "num_highlights": 3},
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncBookManager(client)
            results = await manager.search_books("python")

        assert len(results) == 1
        assert results[0].title is not None
        assert "Python" in results[0].title


class TestAsyncDocumentManager:
    """Tests for AsyncDocumentManager."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_inbox(self, api_key: str) -> None:
        """Test getting inbox documents."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "nextPageCursor": None,
                    "results": [
                        {
                            "id": "doc1",
                            "url": "https://example.com/1",
                            "title": "Inbox Doc",
                            "location": "new",
                        }
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncDocumentManager(client)
            docs = await manager.get_inbox()

        assert len(docs) == 1
        assert docs[0].id == "doc1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_reading_list(self, api_key: str) -> None:
        """Test getting reading list documents."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "nextPageCursor": None,
                    "results": [
                        {
                            "id": "doc2",
                            "url": "https://example.com/2",
                            "title": "Reading Doc",
                            "location": "later",
                        }
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncDocumentManager(client)
            docs = await manager.get_reading_list()

        assert len(docs) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_archive(self, api_key: str) -> None:
        """Test bulk archiving documents."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc1/").mock(
            return_value=httpx.Response(200, json={"id": "doc1", "url": "https://example.com/1"})
        )
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc2/").mock(
            return_value=httpx.Response(200, json={"id": "doc2", "url": "https://example.com/2"})
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncDocumentManager(client)
            results = await manager.bulk_archive(["doc1", "doc2"])

        assert results["doc1"] is True
        assert results["doc2"] is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_documents(self, api_key: str) -> None:
        """Test searching documents."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "nextPageCursor": None,
                    "results": [
                        {
                            "id": "doc1",
                            "url": "https://example.com/1",
                            "title": "Python Tutorial",
                            "location": "new",
                        },
                        {
                            "id": "doc2",
                            "url": "https://example.com/2",
                            "title": "JavaScript Basics",
                            "location": "new",
                        },
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncDocumentManager(client)
            results = await manager.search_documents("python")

        assert len(results) == 1
        assert results[0].title is not None
        assert "Python" in results[0].title


class TestAsyncSyncManager:
    """Tests for AsyncSyncManager."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_full_sync(self, api_key: str) -> None:
        """Test full sync operation."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [{"id": 1, "text": "Highlight"}],
                },
            )
        )
        respx.get(f"{READWISE_API_V2_BASE}/books/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [{"id": 1, "title": "Book", "num_highlights": 1}],
                },
            )
        )
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "nextPageCursor": None,
                    "results": [
                        {
                            "id": "doc1",
                            "url": "https://example.com",
                            "title": "Doc",
                            "location": "new",
                        }
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client)
            result = await manager.full_sync()

        assert len(result.highlights) == 1
        assert len(result.books) == 1
        assert len(result.documents) == 1
        assert manager.state.total_syncs == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_incremental_sync(self, api_key: str) -> None:
        """Test incremental sync operation."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={"next": None, "results": []},
            )
        )
        respx.get(f"{READWISE_API_V2_BASE}/books/").mock(
            return_value=httpx.Response(
                200,
                json={"next": None, "results": []},
            )
        )
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"nextPageCursor": None, "results": []},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client)
            # First sync
            await manager.full_sync()
            # Second sync (incremental)
            result = await manager.incremental_sync()

        assert result.is_empty
        assert manager.state.total_syncs == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_highlights_only(self, api_key: str) -> None:
        """Test syncing only highlights."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [{"id": 1, "text": "Highlight"}],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client)
            result = await manager.sync_highlights_only()

        assert len(result.highlights) == 1
        assert len(result.books) == 0
        assert len(result.documents) == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_callback(self, api_key: str) -> None:
        """Test sync callback notification."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json={"next": None, "results": []},
            )
        )
        respx.get(f"{READWISE_API_V2_BASE}/books/").mock(
            return_value=httpx.Response(
                200,
                json={"next": None, "results": []},
            )
        )
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"nextPageCursor": None, "results": []},
            )
        )

        callback_called = []

        def callback(result):
            callback_called.append(result)

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client)
            manager.on_sync(callback)
            await manager.full_sync()

        assert len(callback_called) == 1

    @pytest.mark.asyncio
    async def test_reset_state(self, api_key: str) -> None:
        """Test resetting sync state."""
        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client)
            # Manually set some state
            manager._state.total_syncs = 5
            manager._state.last_highlight_sync = datetime.now(UTC)

            manager.reset_state()

        assert manager.state.total_syncs == 0
        assert manager.state.last_highlight_sync is None
