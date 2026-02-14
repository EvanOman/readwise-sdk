"""Tests for DocumentManager."""

import json

import httpx
import pytest
import respx

from readwise_sdk.client import READWISE_API_V3_BASE, ReadwiseClient
from readwise_sdk.managers.documents import DocumentManager
from readwise_sdk.v3.models import DocumentCategory

V3_LIST = f"{READWISE_API_V3_BASE}/list/"
V3_UPDATE = f"{READWISE_API_V3_BASE}/update/"


def _make_manager(api_key: str) -> DocumentManager:
    return DocumentManager(ReadwiseClient(api_key=api_key))


def _mock_list_response(results: list[dict], *, cursor: str | None = None) -> None:
    respx.get(V3_LIST).mock(
        return_value=httpx.Response(200, json={"results": results, "nextPageCursor": cursor})
    )


class TestDocumentManager:
    """Tests for DocumentManager."""

    @respx.mock
    def test_get_inbox(self, api_key: str) -> None:
        """Test getting inbox documents."""
        route = respx.get(V3_LIST).mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://example.com/1", "location": "new"},
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        docs = _make_manager(api_key).get_inbox()

        assert len(docs) == 1
        assert "location=new" in str(route.calls.last.request.url)

    @respx.mock
    def test_get_reading_list(self, api_key: str) -> None:
        """Test getting reading list documents."""
        route = respx.get(V3_LIST).mock(
            return_value=httpx.Response(200, json={"results": [], "nextPageCursor": None})
        )

        _make_manager(api_key).get_reading_list()

        assert "location=later" in str(route.calls.last.request.url)

    @respx.mock
    def test_bulk_archive(self, api_key: str) -> None:
        """Test bulk archiving documents."""
        respx.patch(url__startswith=V3_UPDATE).mock(
            return_value=httpx.Response(
                200, json={"id": "doc1", "url": "https://readwise.io/reader/doc1"}
            )
        )

        results = _make_manager(api_key).bulk_archive(["doc1", "doc2"])

        assert results == {"doc1": True, "doc2": True}

    @respx.mock
    def test_search_documents(self, api_key: str) -> None:
        """Test searching documents."""
        _mock_list_response(
            [
                {"id": "doc1", "url": "https://a.com", "title": "Python Tutorial"},
                {"id": "doc2", "url": "https://b.com", "title": "JavaScript Guide"},
            ]
        )

        results = _make_manager(api_key).search_documents("python")

        assert len(results) == 1
        assert results[0].title is not None
        assert "Python" in results[0].title

    @respx.mock
    def test_get_inbox_stats(self, api_key: str) -> None:
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

        stats = _make_manager(api_key).get_inbox_stats()

        assert stats.inbox_count == 2
        assert stats.reading_list_count == 1
        assert stats.by_category["article"] == 3

    @respx.mock
    def test_get_documents_by_category(self, api_key: str) -> None:
        """Test getting documents by category."""
        route = respx.get(V3_LIST).mock(
            return_value=httpx.Response(200, json={"results": [], "nextPageCursor": None})
        )

        _make_manager(api_key).get_documents_by_category(DocumentCategory.ARTICLE)

        assert "category=article" in str(route.calls.last.request.url)

    @respx.mock
    def test_get_archive(self, api_key: str) -> None:
        """Test getting archived documents."""
        route = respx.get(V3_LIST).mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://example.com/1", "location": "archive"},
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        docs = _make_manager(api_key).get_archive()

        assert len(docs) == 1
        assert "location=archive" in str(route.calls.last.request.url)

    @respx.mock
    @pytest.mark.parametrize(
        ("kwargs", "description"),
        [
            ({"days": 7}, "days"),
            ({"hours": 24}, "hours"),
        ],
    )
    def test_get_documents_since(self, api_key: str, kwargs: dict, description: str) -> None:
        """Test getting documents since N days/hours ago."""
        route = respx.get(V3_LIST).mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [{"id": "doc1", "url": "https://example.com/1"}],
                    "nextPageCursor": None,
                },
            )
        )

        docs = _make_manager(api_key).get_documents_since(**kwargs)

        assert len(docs) == 1
        assert "updatedAfter" in str(route.calls.last.request.url)

    def test_get_documents_since_error(self, api_key: str) -> None:
        """Test that get_documents_since raises when no time arg is given."""
        with pytest.raises(ValueError, match="Must specify days, hours, or since"):
            _make_manager(api_key).get_documents_since()

    @respx.mock
    @pytest.mark.parametrize(
        ("method", "expected_location"),
        [
            ("move_to_later", "later"),
            ("archive", "archive"),
            ("move_to_inbox", "new"),
        ],
    )
    def test_document_move_operations(
        self, api_key: str, method: str, expected_location: str
    ) -> None:
        """Test moving a document to different locations."""
        route = respx.patch(f"{V3_UPDATE}doc1/").mock(
            return_value=httpx.Response(200, json={"id": "doc1", "url": "https://example.com/1"})
        )

        manager = _make_manager(api_key)
        getattr(manager, method)("doc1")

        assert route.called
        body = json.loads(route.calls[0].request.content)
        assert body["location"] == expected_location

    @respx.mock
    def test_bulk_tag_documents(self, api_key: str) -> None:
        """Test bulk tagging documents - success path."""
        respx.patch(url__startswith=V3_UPDATE).mock(
            return_value=httpx.Response(200, json={"id": "doc1", "url": "https://example.com/1"})
        )

        results = _make_manager(api_key).bulk_tag_documents(["doc1", "doc2"], ["tag1", "tag2"])

        assert results == {"doc1": True, "doc2": True}

    @respx.mock
    def test_bulk_tag_documents_exception_path(self, api_key: str) -> None:
        """Test bulk tagging documents when API call raises an exception."""
        respx.patch(url__startswith=V3_UPDATE).mock(return_value=httpx.Response(500))

        assert _make_manager(api_key).bulk_tag_documents(["doc1"], ["tag1"]) == {"doc1": False}

    @respx.mock
    def test_filter_documents(self, api_key: str) -> None:
        """Test filtering documents with a predicate."""
        _mock_list_response(
            [
                {"id": "doc1", "url": "https://a.com", "title": "Short"},
                {"id": "doc2", "url": "https://b.com", "title": "A much longer document title"},
            ]
        )

        results = list(
            _make_manager(api_key).filter_documents(
                lambda d: d.title is not None and len(d.title) > 10
            )
        )

        assert len(results) == 1
        assert results[0].id == "doc2"

    @respx.mock
    def test_get_unread_count(self, api_key: str) -> None:
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

        assert _make_manager(api_key).get_unread_count() == 3

    @respx.mock
    def test_bulk_archive_exception_path(self, api_key: str) -> None:
        """Test bulk archiving when API call raises an exception."""
        respx.patch(url__startswith=V3_UPDATE).mock(return_value=httpx.Response(500))

        assert _make_manager(api_key).bulk_archive(["doc1", "doc2"]) == {
            "doc1": False,
            "doc2": False,
        }
