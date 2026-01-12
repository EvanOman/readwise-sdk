"""Tests for Readwise Reader API v3 client."""

import httpx
import pytest
import respx

from readwise_sdk.client import READWISE_API_V3_BASE, ReadwiseClient
from readwise_sdk.exceptions import NotFoundError
from readwise_sdk.v3.models import (
    DocumentCategory,
    DocumentCreate,
    DocumentLocation,
    DocumentUpdate,
)


class TestV3ClientAccess:
    """Tests for accessing v3 client from main client."""

    def test_v3_property(self, api_key: str) -> None:
        """Test that v3 property returns the v3 client."""
        client = ReadwiseClient(api_key=api_key)
        assert client.v3 is not None

    def test_v3_property_cached(self, api_key: str) -> None:
        """Test that v3 client is cached."""
        client = ReadwiseClient(api_key=api_key)
        v3_first = client.v3
        v3_second = client.v3
        assert v3_first is v3_second


class TestDocuments:
    """Tests for document operations."""

    @respx.mock
    def test_list_documents(self, api_key: str) -> None:
        """Test listing documents."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://example.com/1", "title": "Article 1"},
                        {"id": "doc2", "url": "https://example.com/2", "title": "Article 2"},
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        client = ReadwiseClient(api_key=api_key)
        documents = list(client.v3.list_documents())

        assert len(documents) == 2
        assert documents[0].id == "doc1"
        assert documents[0].title == "Article 1"

    @respx.mock
    def test_list_documents_with_filters(self, api_key: str) -> None:
        """Test listing documents with filters."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        list(
            client.v3.list_documents(
                location=DocumentLocation.NEW,
                category=DocumentCategory.ARTICLE,
            )
        )

        assert route.called
        request = route.calls.last.request
        assert "location=new" in str(request.url)
        assert "category=article" in str(request.url)

    @respx.mock
    def test_get_document(self, api_key: str) -> None:
        """Test getting a single document."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": "doc123",
                            "url": "https://example.com/article",
                            "title": "Test Article",
                            "word_count": 1000,
                        }
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        client = ReadwiseClient(api_key=api_key)
        doc = client.v3.get_document("doc123")

        assert doc is not None
        assert doc.id == "doc123"
        assert doc.title == "Test Article"
        assert doc.word_count == 1000

    @respx.mock
    def test_get_document_not_found(self, api_key: str) -> None:
        """Test getting a non-existent document."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        doc = client.v3.get_document("nonexistent")

        assert doc is None

    @respx.mock
    def test_create_document(self, api_key: str) -> None:
        """Test creating a document."""
        respx.post(f"{READWISE_API_V3_BASE}/save/").mock(
            return_value=httpx.Response(
                201,
                json={"id": "new123", "url": "https://readwise.io/reader/new123"},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        doc = DocumentCreate(
            url="https://example.com/new-article",
            title="New Article",
            tags=["tech"],
        )
        result = client.v3.create_document(doc)

        assert result.id == "new123"

    @respx.mock
    def test_save_url(self, api_key: str) -> None:
        """Test saving a URL."""
        respx.post(f"{READWISE_API_V3_BASE}/save/").mock(
            return_value=httpx.Response(
                201,
                json={"id": "saved123", "url": "https://readwise.io/reader/saved123"},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        result = client.v3.save_url(
            "https://example.com/article",
            location=DocumentLocation.LATER,
            tags=["important"],
        )

        assert result.id == "saved123"

    @respx.mock
    def test_update_document(self, api_key: str) -> None:
        """Test updating a document."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://readwise.io/reader/doc123"},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        update = DocumentUpdate(title="Updated Title")
        result = client.v3.update_document("doc123", update)

        assert result.id == "doc123"

    @respx.mock
    def test_delete_document(self, api_key: str) -> None:
        """Test deleting a document."""
        respx.delete(f"{READWISE_API_V3_BASE}/delete/doc123/").mock(
            return_value=httpx.Response(204)
        )

        client = ReadwiseClient(api_key=api_key)
        client.v3.delete_document("doc123")  # Should not raise


class TestDocumentMovement:
    """Tests for document location operations."""

    @respx.mock
    def test_move_to_later(self, api_key: str) -> None:
        """Test moving document to later."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://readwise.io/reader/doc123"},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        result = client.v3.move_to_later("doc123")

        assert result.id == "doc123"

    @respx.mock
    def test_archive(self, api_key: str) -> None:
        """Test archiving a document."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://readwise.io/reader/doc123"},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        result = client.v3.archive("doc123")

        assert result.id == "doc123"

    @respx.mock
    def test_move_to_inbox(self, api_key: str) -> None:
        """Test moving document back to inbox."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://readwise.io/reader/doc123"},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        result = client.v3.move_to_inbox("doc123")

        assert result.id == "doc123"


class TestTags:
    """Tests for tag operations."""

    @respx.mock
    def test_list_tags(self, api_key: str) -> None:
        """Test listing tags."""
        respx.get(f"{READWISE_API_V3_BASE}/tags/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"key": "tech", "name": "tech"},
                        {"key": "work", "name": "work"},
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        client = ReadwiseClient(api_key=api_key)
        tags = list(client.v3.list_tags())

        assert len(tags) == 2
        assert tags[0].name == "tech"

    @respx.mock
    def test_tag_document(self, api_key: str) -> None:
        """Test setting tags on a document."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://readwise.io/reader/doc123"},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        result = client.v3.tag_document("doc123", ["new-tag", "another"])

        assert result.id == "doc123"

    @respx.mock
    def test_add_tag(self, api_key: str) -> None:
        """Test adding a tag to a document."""
        # First call to get document
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc123", "url": "https://example.com", "tags": ["existing"]}
                    ],
                    "nextPageCursor": None,
                },
            )
        )
        # Second call to update
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://readwise.io/reader/doc123"},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        result = client.v3.add_tag("doc123", "new-tag")

        assert result.id == "doc123"

    @respx.mock
    def test_add_tag_not_found(self, api_key: str) -> None:
        """Test adding a tag to non-existent document."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        with pytest.raises(NotFoundError):
            client.v3.add_tag("nonexistent", "tag")


class TestConvenienceMethods:
    """Tests for convenience methods."""

    @respx.mock
    def test_get_inbox(self, api_key: str) -> None:
        """Test getting inbox documents."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        list(client.v3.get_inbox())

        assert route.called
        request = route.calls.last.request
        assert "location=new" in str(request.url)

    @respx.mock
    def test_get_reading_list(self, api_key: str) -> None:
        """Test getting reading list documents."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        list(client.v3.get_reading_list())

        assert route.called
        request = route.calls.last.request
        assert "location=later" in str(request.url)

    @respx.mock
    def test_get_archive(self, api_key: str) -> None:
        """Test getting archived documents."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        client = ReadwiseClient(api_key=api_key)
        list(client.v3.get_archive())

        assert route.called
        request = route.calls.last.request
        assert "location=archive" in str(request.url)
