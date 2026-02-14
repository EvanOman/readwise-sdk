"""Tests for async Readwise Reader API v3 client."""

import asyncio

import httpx
import pytest
import respx

from readwise_sdk import AsyncReadwiseClient
from readwise_sdk.client import READWISE_API_V3_BASE
from readwise_sdk.exceptions import NotFoundError
from readwise_sdk.v3.models import DocumentCategory, DocumentLocation, DocumentUpdate


class TestAsyncV3Documents:
    """Tests for async document operations."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_documents(self, api_key: str) -> None:
        """Test listing documents asynchronously."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://example.com/1", "title": "Doc One"},
                        {"id": "doc2", "url": "https://example.com/2", "title": "Doc Two"},
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = [doc async for doc in client.v3.list_documents()]

            assert len(docs) == 2
            assert docs[0].id == "doc1"
            assert docs[0].title == "Doc One"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_documents_with_filters(self, api_key: str) -> None:
        """Test listing documents with filters."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            _ = [
                doc
                async for doc in client.v3.list_documents(
                    location=DocumentLocation.NEW,
                    category=DocumentCategory.ARTICLE,
                )
            ]

            assert route.called
            request = route.calls.last.request
            assert "location=new" in str(request.url)
            assert "category=article" in str(request.url)

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_documents_with_tags(self, api_key: str) -> None:
        """Test listing documents filtered by tags."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            _ = [doc async for doc in client.v3.list_documents(tags=["python"])]

            assert route.called
            request = route.calls.last.request
            assert "tag=python" in str(request.url)

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_documents_with_content(self, api_key: str) -> None:
        """Test listing documents with with_content parameter."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": "doc1",
                            "url": "https://example.com/1",
                            "title": "Article 1",
                            "html_content": "<p>Content</p>",
                        }
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = [doc async for doc in client.v3.list_documents(with_content=True)]

            assert route.called
            request = route.calls.last.request
            assert "withHtmlContent=true" in str(request.url)
            assert len(docs) == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_document(self, api_key: str) -> None:
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
                            "author": "Test Author",
                        }
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            doc = await client.v3.get_document("doc123")

            assert doc is not None
            assert doc.id == "doc123"
            assert doc.title == "Test Article"

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, api_key: str) -> None:
        """Test getting a non-existent document returns None."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            doc = await client.v3.get_document("nonexistent")
            assert doc is None

    @respx.mock
    @pytest.mark.asyncio
    async def test_save_url(self, api_key: str) -> None:
        """Test saving a URL."""
        respx.post(f"{READWISE_API_V3_BASE}/save/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "new_doc_123",
                    "url": "https://example.com/article",
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await client.v3.save_url("https://example.com/article")

            assert result.id == "new_doc_123"
            assert result.url == "https://example.com/article"

    @respx.mock
    @pytest.mark.asyncio
    async def test_update_document(self, api_key: str) -> None:
        """Test updating a document."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "id": "doc123",
                    "url": "https://example.com/article",
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            update = DocumentUpdate(location=DocumentLocation.ARCHIVE)
            result = await client.v3.update_document("doc123", update)

            assert result.id == "doc123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_delete_document(self, api_key: str) -> None:
        """Test deleting a document."""
        respx.delete(f"{READWISE_API_V3_BASE}/delete/doc123/").mock(
            return_value=httpx.Response(204)
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            await client.v3.delete_document("doc123")  # Should not raise


class TestAsyncV3DocumentMovement:
    """Tests for async document movement operations."""

    @respx.mock
    @pytest.mark.asyncio
    @pytest.mark.parametrize("method", ["move_to_later", "archive", "move_to_inbox"])
    async def test_movement_methods(self, api_key: str, method: str) -> None:
        """Test document movement methods all update the document and return it."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://example.com"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await getattr(client.v3, method)("doc123")
            assert result.id == "doc123"


class TestAsyncV3Tags:
    """Tests for async tag operations."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_tags(self, api_key: str) -> None:
        """Test listing tags."""
        respx.get(f"{READWISE_API_V3_BASE}/tags/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"key": "tag1", "name": "Tag One"},
                        {"key": "tag2", "name": "Tag Two"},
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            tags = [tag async for tag in client.v3.list_tags()]

            assert len(tags) == 2
            assert tags[0].name == "Tag One"

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_tag(self, api_key: str) -> None:
        """Test adding a tag to a document."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": "doc123",
                            "url": "https://example.com",
                            "title": "Test",
                            "tags": ["existing-tag"],
                        }
                    ],
                    "nextPageCursor": None,
                },
            )
        )
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://example.com"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await client.v3.add_tag("doc123", "new-tag")
            assert result.id == "doc123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_remove_tag(self, api_key: str) -> None:
        """Test removing a tag from a document."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": "doc123",
                            "url": "https://example.com",
                            "tags": ["keep-me", "remove-me"],
                        }
                    ],
                    "nextPageCursor": None,
                },
            )
        )
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://readwise.io/reader/doc123"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await client.v3.remove_tag("doc123", "remove-me")
            assert result.id == "doc123"

    @respx.mock
    @pytest.mark.asyncio
    @pytest.mark.parametrize("method", ["remove_tag", "add_tag"])
    async def test_tag_operation_not_found(self, api_key: str, method: str) -> None:
        """Test that tag operations raise NotFoundError for non-existent documents."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            with pytest.raises(NotFoundError):
                await getattr(client.v3, method)("nonexistent", "tag")


class TestAsyncV3ConvenienceMethods:
    """Tests for async convenience methods."""

    @respx.mock
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("method", "expected_param"),
        [
            ("get_inbox", "location=new"),
            ("get_reading_list", "location=later"),
            ("get_archive", "location=archive"),
            ("get_articles", "category=article"),
        ],
    )
    async def test_convenience_methods(
        self, api_key: str, method: str, expected_param: str
    ) -> None:
        """Test convenience methods pass the correct query parameters."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [{"id": "doc1", "url": "https://example.com/1", "title": "Doc 1"}],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = [doc async for doc in getattr(client.v3, method)()]

            assert len(docs) == 1
            assert route.called
            request = route.calls.last.request
            assert expected_param in str(request.url)


class TestAsyncConcurrency:
    """Tests for concurrent async operations."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_concurrent_document_fetches(self, api_key: str) -> None:
        """Test fetching multiple documents concurrently."""
        for doc_id in ["doc1", "doc2", "doc3"]:
            respx.get(
                f"{READWISE_API_V3_BASE}/list/",
                params={"id": doc_id},
            ).mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "id": doc_id,
                                "url": f"https://example.com/{doc_id}",
                                "title": f"Doc {doc_id}",
                            }
                        ],
                        "nextPageCursor": None,
                    },
                )
            )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = await asyncio.gather(
                client.v3.get_document("doc1"),
                client.v3.get_document("doc2"),
                client.v3.get_document("doc3"),
            )

            assert len(docs) == 3
            assert all(doc is not None for doc in docs)
            for i, doc_id in enumerate(["doc1", "doc2", "doc3"]):
                doc = docs[i]
                assert doc is not None
                assert doc.id == doc_id

    @respx.mock
    @pytest.mark.asyncio
    async def test_concurrent_url_saves(self, api_key: str) -> None:
        """Test saving multiple URLs concurrently."""
        respx.post(f"{READWISE_API_V3_BASE}/save/").mock(
            side_effect=[
                httpx.Response(200, json={"id": "new1", "url": "https://example.com/1"}),
                httpx.Response(200, json={"id": "new2", "url": "https://example.com/2"}),
                httpx.Response(200, json={"id": "new3", "url": "https://example.com/3"}),
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            results = await asyncio.gather(
                client.v3.save_url("https://example.com/1"),
                client.v3.save_url("https://example.com/2"),
                client.v3.save_url("https://example.com/3"),
            )

            assert len(results) == 3
            for i, expected_id in enumerate(["new1", "new2", "new3"]):
                assert results[i].id == expected_id
