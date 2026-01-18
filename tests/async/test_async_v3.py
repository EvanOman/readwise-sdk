"""Tests for async Readwise Reader API v3 client."""

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
            docs = []
            async for doc in client.v3.list_documents():
                docs.append(doc)

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
            docs = []
            async for doc in client.v3.list_documents(
                location=DocumentLocation.NEW,
                category=DocumentCategory.ARTICLE,
            ):
                docs.append(doc)

            assert route.called
            request = route.calls.last.request
            assert "location=new" in str(request.url)
            assert "category=article" in str(request.url)

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
    async def test_move_to_later(self, api_key: str) -> None:
        """Test moving document to reading list."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://example.com"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await client.v3.move_to_later("doc123")
            assert result.id == "doc123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_archive(self, api_key: str) -> None:
        """Test archiving a document."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://example.com"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await client.v3.archive("doc123")
            assert result.id == "doc123"

    @respx.mock
    @pytest.mark.asyncio
    async def test_move_to_inbox(self, api_key: str) -> None:
        """Test moving document to inbox."""
        respx.patch(f"{READWISE_API_V3_BASE}/update/doc123/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "doc123", "url": "https://example.com"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await client.v3.move_to_inbox("doc123")
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
            tags = []
            async for tag in client.v3.list_tags():
                tags.append(tag)

            assert len(tags) == 2
            assert tags[0].name == "Tag One"

    @respx.mock
    @pytest.mark.asyncio
    async def test_add_tag(self, api_key: str) -> None:
        """Test adding a tag to a document."""
        # First mock get_document to return existing tags
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

        # Then mock the update
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
    async def test_add_tag_not_found(self, api_key: str) -> None:
        """Test adding tag to non-existent document."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            with pytest.raises(NotFoundError):
                await client.v3.add_tag("nonexistent", "tag")


class TestAsyncV3ConvenienceMethods:
    """Tests for async convenience methods."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_inbox(self, api_key: str) -> None:
        """Test getting inbox documents."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://example.com/1", "title": "Inbox Doc"}
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = []
            async for doc in client.v3.get_inbox():
                docs.append(doc)

            assert len(docs) == 1
            assert route.called
            request = route.calls.last.request
            assert "location=new" in str(request.url)

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_reading_list(self, api_key: str) -> None:
        """Test getting reading list documents."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://example.com/1", "title": "Later Doc"}
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = []
            async for doc in client.v3.get_reading_list():
                docs.append(doc)

            assert len(docs) == 1
            assert route.called
            request = route.calls.last.request
            assert "location=later" in str(request.url)

    @respx.mock
    @pytest.mark.asyncio
    async def test_get_archive(self, api_key: str) -> None:
        """Test getting archived documents."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://example.com/1", "title": "Archived Doc"}
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            docs = []
            async for doc in client.v3.get_archive():
                docs.append(doc)

            assert len(docs) == 1
            assert route.called
            request = route.calls.last.request
            assert "location=archive" in str(request.url)


class TestAsyncConcurrency:
    """Tests for concurrent async operations."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_concurrent_document_fetches(self, api_key: str) -> None:
        """Test fetching multiple documents concurrently."""
        import asyncio

        # Set up mocks for different document IDs
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
            # Fetch all documents concurrently
            docs = await asyncio.gather(
                client.v3.get_document("doc1"),
                client.v3.get_document("doc2"),
                client.v3.get_document("doc3"),
            )

            assert len(docs) == 3
            assert all(doc is not None for doc in docs)
            # Type checker needs explicit None checks
            assert docs[0] is not None and docs[0].id == "doc1"
            assert docs[1] is not None and docs[1].id == "doc2"
            assert docs[2] is not None and docs[2].id == "doc3"

    @respx.mock
    @pytest.mark.asyncio
    async def test_concurrent_url_saves(self, api_key: str) -> None:
        """Test saving multiple URLs concurrently."""
        import asyncio

        # Mock save endpoint to return incrementing IDs
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
            assert results[0].id == "new1"
            assert results[1].id == "new2"
            assert results[2].id == "new3"
