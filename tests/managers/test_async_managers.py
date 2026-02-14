"""Tests for async manager classes."""

import json
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
from readwise_sdk.v3.models import DocumentCategory

V2_HIGHLIGHTS = f"{READWISE_API_V2_BASE}/highlights/"
V2_BOOKS = f"{READWISE_API_V2_BASE}/books/"
V3_LIST = f"{READWISE_API_V3_BASE}/list/"
V3_UPDATE = f"{READWISE_API_V3_BASE}/update/"


def _mock_v2_highlights(results: list[dict]) -> None:
    respx.get(V2_HIGHLIGHTS).mock(
        return_value=httpx.Response(200, json={"next": None, "results": results})
    )


def _mock_v2_books(results: list[dict]) -> None:
    respx.get(V2_BOOKS).mock(
        return_value=httpx.Response(200, json={"next": None, "results": results})
    )


def _mock_v3_list(results: list[dict]) -> None:
    respx.get(V3_LIST).mock(
        return_value=httpx.Response(200, json={"nextPageCursor": None, "results": results})
    )


def _mock_empty_sync_responses() -> None:
    """Mock all three sync endpoints with empty results."""
    _mock_v2_highlights([])
    _mock_v2_books([])
    _mock_v3_list([])


class TestAsyncHighlightManager:
    """Tests for AsyncHighlightManager."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_all_highlights(self, api_key: str) -> None:
        """Test getting all highlights."""
        _mock_v2_highlights([{"id": 1, "text": "First"}, {"id": 2, "text": "Second"}])

        async with AsyncReadwiseClient(api_key=api_key) as client:
            highlights = await AsyncHighlightManager(client).get_all_highlights()

        assert len(highlights) == 2
        assert highlights[0].id == 1
        assert highlights[1].id == 2

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize(
        ("kwargs", "description"),
        [
            ({"days": 7}, "days"),
            ({"hours": 24}, "hours"),
        ],
    )
    async def test_get_highlights_since(self, api_key: str, kwargs: dict, description: str) -> None:
        """Test getting highlights since N days/hours ago."""
        _mock_v2_highlights([{"id": 1, "text": "Recent"}])

        async with AsyncReadwiseClient(api_key=api_key) as client:
            highlights = await AsyncHighlightManager(client).get_highlights_since(**kwargs)

        assert len(highlights) == 1

    @pytest.mark.asyncio
    async def test_get_highlights_since_error(self, api_key: str) -> None:
        """Test that get_highlights_since raises when no time arg is given."""
        async with AsyncReadwiseClient(api_key=api_key) as client:
            with pytest.raises(ValueError, match="Must specify days, hours, or since"):
                await AsyncHighlightManager(client).get_highlights_since()

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_highlights_by_book(self, api_key: str) -> None:
        """Test getting highlights by book ID."""
        _mock_v2_highlights([{"id": 1, "text": "Book highlight", "book_id": 42}])

        async with AsyncReadwiseClient(api_key=api_key) as client:
            highlights = await AsyncHighlightManager(client).get_highlights_by_book(42)

        assert len(highlights) == 1
        assert highlights[0].book_id == 42

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_highlights_with_notes(self, api_key: str) -> None:
        """Test getting highlights that have notes."""
        _mock_v2_highlights(
            [
                {"id": 1, "text": "No note", "note": None},
                {"id": 2, "text": "Has note", "note": "My note"},
                {"id": 3, "text": "Empty note", "note": ""},
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            highlights = await AsyncHighlightManager(client).get_highlights_with_notes()

        assert len(highlights) == 1
        assert highlights[0].id == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_highlights(self, api_key: str) -> None:
        """Test searching highlights."""
        _mock_v2_highlights(
            [
                {"id": 1, "text": "Python is great"},
                {"id": 2, "text": "JavaScript too"},
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncHighlightManager(client).search_highlights("python")

        assert len(results) == 1
        assert "Python" in results[0].text

    @pytest.mark.asyncio
    @respx.mock
    async def test_filter_highlights(self, api_key: str) -> None:
        """Test filtering highlights with a predicate."""
        _mock_v2_highlights(
            [
                {"id": 1, "text": "Short"},
                {"id": 2, "text": "This is a much longer highlight text"},
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncHighlightManager(client)
            results = [h async for h in manager.filter_highlights(lambda h: len(h.text) > 10)]

        assert len(results) == 1
        assert results[0].id == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_tag(self, api_key: str) -> None:
        """Test bulk tagging highlights."""
        respx.post(url__startswith=V2_HIGHLIGHTS).mock(
            return_value=httpx.Response(200, json={"id": 1, "name": "test-tag"})
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncHighlightManager(client).bulk_tag([1, 2], "test-tag")

        assert results == {1: True, 2: True}

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_tag_exception_path(self, api_key: str) -> None:
        """Test bulk tagging when API call raises an exception."""
        respx.post(url__startswith=V2_HIGHLIGHTS).mock(return_value=httpx.Response(500))

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncHighlightManager(client).bulk_tag([1], "test-tag")

        assert results == {1: False}

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_untag_success(self, api_key: str) -> None:
        """Test bulk untagging highlights - success path."""
        respx.get(f"{V2_HIGHLIGHTS}1/tags/").mock(
            return_value=httpx.Response(
                200, json={"results": [{"id": 10, "name": "test-tag"}], "next": None}
            )
        )
        respx.delete(f"{V2_HIGHLIGHTS}1/tags/10/").mock(return_value=httpx.Response(204))

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncHighlightManager(client).bulk_untag([1], "test-tag")

        assert results == {1: True}

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_untag_no_matching_tag(self, api_key: str) -> None:
        """Test bulk untagging when tag does not exist on highlight."""
        respx.get(f"{V2_HIGHLIGHTS}1/tags/").mock(
            return_value=httpx.Response(
                200, json={"results": [{"id": 10, "name": "other-tag"}], "next": None}
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncHighlightManager(client).bulk_untag([1], "test-tag")

        assert results == {1: True}

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_untag_exception_path(self, api_key: str) -> None:
        """Test bulk untagging when API call raises an exception."""
        respx.get(f"{V2_HIGHLIGHTS}1/tags/").mock(return_value=httpx.Response(500))

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncHighlightManager(client).bulk_untag([1], "test-tag")

        assert results == {1: False}

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_highlight(self, api_key: str) -> None:
        """Test creating a highlight."""
        respx.post(V2_HIGHLIGHTS).mock(
            return_value=httpx.Response(200, json=[{"modified_highlights": [999]}])
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            highlight_id = await AsyncHighlightManager(client).create_highlight(
                text="New highlight", title="Test Book"
            )

        assert highlight_id == 999

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_highlight_count(self, api_key: str) -> None:
        """Test getting highlight count."""
        _mock_v2_highlights(
            [
                {"id": 1, "text": "One"},
                {"id": 2, "text": "Two"},
                {"id": 3, "text": "Three"},
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            count = await AsyncHighlightManager(client).get_highlight_count()

        assert count == 3


class TestAsyncBookManager:
    """Tests for AsyncBookManager."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_all_books(self, api_key: str) -> None:
        """Test getting all books."""
        _mock_v2_books(
            [
                {"id": 1, "title": "Book 1", "num_highlights": 5},
                {"id": 2, "title": "Book 2", "num_highlights": 3},
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            books = await AsyncBookManager(client).get_all_books()

        assert len(books) == 2
        assert books[0].title == "Book 1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_books_by_category(self, api_key: str) -> None:
        """Test getting books by category."""
        _mock_v2_books([{"id": 1, "title": "Article", "category": "articles", "num_highlights": 2}])

        async with AsyncReadwiseClient(api_key=api_key) as client:
            books = await AsyncBookManager(client).get_books_by_category(BookCategory.ARTICLES)

        assert len(books) == 1
        assert books[0].category == BookCategory.ARTICLES

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_books_by_source(self, api_key: str) -> None:
        """Test getting books by source."""
        route = respx.get(V2_BOOKS).mock(
            return_value=httpx.Response(
                200,
                json={
                    "next": None,
                    "results": [
                        {"id": 1, "title": "Kindle Book", "source": "kindle", "num_highlights": 3}
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            books = await AsyncBookManager(client).get_books_by_source("kindle")

        assert len(books) == 1
        assert books[0].source == "kindle"
        assert "source=kindle" in str(route.calls.last.request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_recent_books(self, api_key: str) -> None:
        """Test getting recently updated books."""
        _mock_v2_books(
            [
                {
                    "id": 1,
                    "title": "Book A",
                    "num_highlights": 5,
                    "last_highlight_at": "2024-06-01T00:00:00Z",
                },
                {
                    "id": 2,
                    "title": "Book B",
                    "num_highlights": 3,
                    "last_highlight_at": "2024-06-15T00:00:00Z",
                },
                {
                    "id": 3,
                    "title": "Book C",
                    "num_highlights": 1,
                    "last_highlight_at": "2024-06-10T00:00:00Z",
                },
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            books = await AsyncBookManager(client).get_recent_books(days=30, limit=2)

        assert len(books) == 2
        assert books[0].title == "Book B"
        assert books[1].title == "Book C"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_book_with_highlights(self, api_key: str) -> None:
        """Test getting a book with its highlights."""
        respx.get(f"{V2_BOOKS}1/").mock(
            return_value=httpx.Response(
                200, json={"id": 1, "title": "Test Book", "num_highlights": 2}
            )
        )
        _mock_v2_highlights(
            [
                {"id": 1, "text": "Highlight 1", "book_id": 1},
                {"id": 2, "text": "Highlight 2", "book_id": 1},
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await AsyncBookManager(client).get_book_with_highlights(1)

        assert result.book.id == 1
        assert len(result.highlights) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_reading_stats(self, api_key: str) -> None:
        """Test getting aggregated reading statistics."""
        _mock_v2_books(
            [
                {
                    "id": 1,
                    "title": "Python Book",
                    "category": "books",
                    "source": "kindle",
                    "num_highlights": 10,
                    "last_highlight_at": "2024-06-01T00:00:00Z",
                },
                {
                    "id": 2,
                    "title": "Article",
                    "category": "articles",
                    "source": "instapaper",
                    "num_highlights": 5,
                    "last_highlight_at": "2024-06-15T00:00:00Z",
                },
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            stats = await AsyncBookManager(client).get_reading_stats()

        assert stats.total_books == 2
        assert stats.total_highlights == 15
        assert stats.books_by_category == {"books": 1, "articles": 1}
        assert stats.highlights_by_source == {"kindle": 10, "instapaper": 5}
        assert len(stats.most_highlighted_books) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_book_count(self, api_key: str) -> None:
        """Test getting total book count."""
        _mock_v2_books(
            [
                {"id": 1, "title": "Book 1", "num_highlights": 5},
                {"id": 2, "title": "Book 2", "num_highlights": 3},
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            count = await AsyncBookManager(client).get_book_count()

        assert count == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_books(self, api_key: str) -> None:
        """Test searching books."""
        _mock_v2_books(
            [
                {"id": 1, "title": "Python Guide", "num_highlights": 5},
                {"id": 2, "title": "JavaScript Guide", "num_highlights": 3},
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncBookManager(client).search_books("python")

        assert len(results) == 1
        assert results[0].title is not None
        assert "Python" in results[0].title


class TestAsyncDocumentManager:
    """Tests for AsyncDocumentManager."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_inbox(self, api_key: str) -> None:
        """Test getting inbox documents."""
        _mock_v3_list(
            [
                {
                    "id": "doc1",
                    "url": "https://example.com/1",
                    "title": "Inbox Doc",
                    "location": "new",
                }
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = await AsyncDocumentManager(client).get_inbox()

        assert len(docs) == 1
        assert docs[0].id == "doc1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_reading_list(self, api_key: str) -> None:
        """Test getting reading list documents."""
        _mock_v3_list(
            [
                {
                    "id": "doc2",
                    "url": "https://example.com/2",
                    "title": "Reading Doc",
                    "location": "later",
                }
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = await AsyncDocumentManager(client).get_reading_list()

        assert len(docs) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_archive(self, api_key: str) -> None:
        """Test getting archived documents."""
        _mock_v3_list(
            [
                {
                    "id": "doc1",
                    "url": "https://example.com/1",
                    "title": "Archived Doc",
                    "location": "archive",
                }
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = await AsyncDocumentManager(client).get_archive()

        assert len(docs) == 1

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize(
        ("kwargs", "description"),
        [
            ({"days": 7}, "days"),
            ({"hours": 24}, "hours"),
        ],
    )
    async def test_get_documents_since(self, api_key: str, kwargs: dict, description: str) -> None:
        """Test getting documents since N days/hours ago."""
        _mock_v3_list([{"id": "doc1", "url": "https://example.com/1"}])

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = await AsyncDocumentManager(client).get_documents_since(**kwargs)

        assert len(docs) == 1

    @pytest.mark.asyncio
    async def test_get_documents_since_error(self, api_key: str) -> None:
        """Test that get_documents_since raises when no time arg is given."""
        async with AsyncReadwiseClient(api_key=api_key) as client:
            with pytest.raises(ValueError, match="Must specify days, hours, or since"):
                await AsyncDocumentManager(client).get_documents_since()

    @pytest.mark.asyncio
    @respx.mock
    @pytest.mark.parametrize(
        ("method", "expected_location"),
        [
            ("move_to_later", "later"),
            ("archive", "archive"),
            ("move_to_inbox", "new"),
        ],
    )
    async def test_document_move_operations(
        self, api_key: str, method: str, expected_location: str
    ) -> None:
        """Test moving a document to different locations."""
        route = respx.patch(f"{V3_UPDATE}doc1/").mock(
            return_value=httpx.Response(200, json={"id": "doc1", "url": "https://example.com/1"})
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncDocumentManager(client)
            await getattr(manager, method)("doc1")

        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body["location"] == expected_location

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_archive(self, api_key: str) -> None:
        """Test bulk archiving documents."""
        respx.patch(f"{V3_UPDATE}doc1/").mock(
            return_value=httpx.Response(200, json={"id": "doc1", "url": "https://example.com/1"})
        )
        respx.patch(f"{V3_UPDATE}doc2/").mock(
            return_value=httpx.Response(200, json={"id": "doc2", "url": "https://example.com/2"})
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncDocumentManager(client).bulk_archive(["doc1", "doc2"])

        assert results == {"doc1": True, "doc2": True}

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_archive_exception_path(self, api_key: str) -> None:
        """Test bulk archiving when API call raises an exception."""
        respx.patch(url__startswith=V3_UPDATE).mock(return_value=httpx.Response(500))

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncDocumentManager(client).bulk_archive(["doc1", "doc2"])

        assert results == {"doc1": False, "doc2": False}

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_tag_documents(self, api_key: str) -> None:
        """Test bulk tagging documents - success path."""
        respx.patch(url__startswith=V3_UPDATE).mock(
            return_value=httpx.Response(200, json={"id": "doc1", "url": "https://example.com/1"})
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncDocumentManager(client).bulk_tag_documents(
                ["doc1", "doc2"], ["tag1", "tag2"]
            )

        assert results == {"doc1": True, "doc2": True}

    @pytest.mark.asyncio
    @respx.mock
    async def test_bulk_tag_documents_exception_path(self, api_key: str) -> None:
        """Test bulk tagging documents when API call raises an exception."""
        respx.patch(url__startswith=V3_UPDATE).mock(return_value=httpx.Response(500))

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncDocumentManager(client).bulk_tag_documents(["doc1"], ["tag1"])

        assert results == {"doc1": False}

    @pytest.mark.asyncio
    @respx.mock
    async def test_filter_documents(self, api_key: str) -> None:
        """Test filtering documents with a predicate."""
        _mock_v3_list(
            [
                {"id": "doc1", "url": "https://a.com", "title": "Short"},
                {"id": "doc2", "url": "https://b.com", "title": "A much longer document title"},
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncDocumentManager(client)
            results = [
                d
                async for d in manager.filter_documents(
                    lambda d: d.title is not None and len(d.title) > 10
                )
            ]

        assert len(results) == 1
        assert results[0].id == "doc2"

    @pytest.mark.asyncio
    @respx.mock
    async def test_search_documents(self, api_key: str) -> None:
        """Test searching documents."""
        _mock_v3_list(
            [
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
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await AsyncDocumentManager(client).search_documents("python")

        assert len(results) == 1
        assert results[0].title is not None
        assert "Python" in results[0].title

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_inbox_stats(self, api_key: str) -> None:
        """Test getting inbox statistics."""
        call_count = 0

        def mock_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "id": "doc1",
                                "url": "https://a.com",
                                "category": "article",
                                "created_at": "2024-01-10T00:00:00Z",
                            },
                            {
                                "id": "doc2",
                                "url": "https://b.com",
                                "category": "article",
                                "created_at": "2024-01-15T00:00:00Z",
                            },
                        ],
                        "nextPageCursor": None,
                    },
                )
            elif call_count == 2:
                return httpx.Response(
                    200,
                    json={
                        "results": [{"id": "doc3", "url": "https://c.com", "category": "article"}],
                        "nextPageCursor": None,
                    },
                )
            else:
                return httpx.Response(200, json={"results": [], "nextPageCursor": None})

        respx.get(V3_LIST).mock(side_effect=mock_response)

        async with AsyncReadwiseClient(api_key=api_key) as client:
            stats = await AsyncDocumentManager(client).get_inbox_stats()

        assert stats.inbox_count == 2
        assert stats.reading_list_count == 1
        assert stats.archive_count == 0
        assert stats.total_count == 3
        assert stats.by_category["article"] == 3
        assert stats.oldest_inbox_item is not None
        assert stats.oldest_inbox_item.id == "doc1"
        assert stats.newest_inbox_item is not None
        assert stats.newest_inbox_item.id == "doc2"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_documents_by_category(self, api_key: str) -> None:
        """Test getting documents by category."""
        route = respx.get(V3_LIST).mock(
            return_value=httpx.Response(
                200,
                json={
                    "nextPageCursor": None,
                    "results": [
                        {"id": "doc1", "url": "https://example.com/1", "category": "article"}
                    ],
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = await AsyncDocumentManager(client).get_documents_by_category(
                DocumentCategory.ARTICLE
            )

        assert len(docs) == 1
        assert "category=article" in str(route.calls.last.request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_unread_count(self, api_key: str) -> None:
        """Test getting unread document count."""
        call_count = 0

        def mock_response(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {"id": "doc1", "url": "https://a.com"},
                            {"id": "doc2", "url": "https://b.com"},
                        ],
                        "nextPageCursor": None,
                    },
                )
            else:
                return httpx.Response(
                    200,
                    json={
                        "results": [{"id": "doc3", "url": "https://c.com"}],
                        "nextPageCursor": None,
                    },
                )

        respx.get(V3_LIST).mock(side_effect=mock_response)

        async with AsyncReadwiseClient(api_key=api_key) as client:
            count = await AsyncDocumentManager(client).get_unread_count()

        assert count == 3


class TestAsyncSyncManager:
    """Tests for AsyncSyncManager."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_full_sync(self, api_key: str) -> None:
        """Test full sync operation."""
        _mock_v2_highlights([{"id": 1, "text": "Highlight"}])
        _mock_v2_books([{"id": 1, "title": "Book", "num_highlights": 1}])
        _mock_v3_list(
            [{"id": "doc1", "url": "https://example.com", "title": "Doc", "location": "new"}]
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
        _mock_empty_sync_responses()

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client)
            await manager.full_sync()
            result = await manager.incremental_sync()

        assert result.is_empty
        assert manager.state.total_syncs == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_highlights_only(self, api_key: str) -> None:
        """Test syncing only highlights."""
        _mock_v2_highlights([{"id": 1, "text": "Highlight"}])

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await AsyncSyncManager(client).sync_highlights_only()

        assert len(result.highlights) == 1
        assert len(result.books) == 0
        assert len(result.documents) == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_documents_only(self, api_key: str) -> None:
        """Test syncing only documents."""
        _mock_v3_list([{"id": "doc1", "url": "https://example.com", "title": "Doc"}])

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await AsyncSyncManager(client).sync_documents_only()

        assert len(result.documents) == 1
        assert len(result.highlights) == 0
        assert len(result.books) == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_callback(self, api_key: str) -> None:
        """Test sync callback notification."""
        _mock_empty_sync_responses()

        callback_called = []

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client)
            manager.on_sync(callback_called.append)
            await manager.full_sync()

        assert len(callback_called) == 1

    @pytest.mark.asyncio
    @respx.mock
    async def test_sync_callback_error_handling(self, api_key: str) -> None:
        """Test that callback errors don't break the sync."""
        _mock_v2_highlights([{"id": 1, "text": "Highlight"}])
        _mock_v2_books([])
        _mock_v3_list([])

        good_callback_called = []

        def bad_callback(result):
            raise RuntimeError("Callback error")

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client)
            manager.on_sync(bad_callback)
            manager.on_sync(good_callback_called.append)
            result = await manager.full_sync()

        assert len(result.highlights) == 1
        assert len(good_callback_called) == 1

    @pytest.mark.asyncio
    async def test_reset_state(self, api_key: str) -> None:
        """Test resetting sync state."""
        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client)
            manager._state.total_syncs = 5
            manager._state.last_highlight_sync = datetime.now(UTC)

            manager.reset_state()

        assert manager.state.total_syncs == 0
        assert manager.state.last_highlight_sync is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_state_file_persistence(self, api_key: str, tmp_path) -> None:
        """Test that sync state is persisted to file."""
        state_file = tmp_path / "sync_state.json"

        _mock_v2_highlights([{"id": 1, "text": "Highlight"}])
        _mock_v2_books([])
        _mock_v3_list([])

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client, state_file=state_file)
            await manager.full_sync()

        assert state_file.exists()
        state_data = json.loads(state_file.read_text())
        assert state_data["total_syncs"] == 1
        assert state_data["last_highlight_sync"] is not None

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager2 = AsyncSyncManager(client, state_file=state_file)

        assert manager2.state.total_syncs == 1
        assert manager2.state.last_highlight_sync is not None

    @pytest.mark.asyncio
    async def test_state_file_corrupted(self, api_key: str, tmp_path) -> None:
        """Test that corrupted state file is handled gracefully."""
        state_file = tmp_path / "sync_state.json"
        state_file.write_text("not valid json{{{")

        async with AsyncReadwiseClient(api_key=api_key) as client:
            manager = AsyncSyncManager(client, state_file=state_file)

        assert manager.state.total_syncs == 0
        assert manager.state.last_highlight_sync is None
