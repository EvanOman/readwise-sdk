"""Tests for AsyncDocumentImporter."""

from datetime import datetime

import httpx
import pytest
import respx

from readwise_sdk import AsyncReadwiseClient
from readwise_sdk.client import READWISE_API_V3_BASE
from readwise_sdk.contrib.document_import import AsyncDocumentImporter


class TestAsyncDocumentImporter:
    """Tests for AsyncDocumentImporter."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_import_document(self, api_key: str) -> None:
        """Test importing a single document."""
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
                            "category": "article",
                            "location": "new",
                            "tags": [],
                        }
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            importer = AsyncDocumentImporter(client)
            doc = await importer.import_document("doc123")

        assert doc.id == "doc123"
        assert doc.title == "Test Article"
        assert doc.domain == "example.com"

    @pytest.mark.asyncio
    @respx.mock
    async def test_import_document_not_found(self, api_key: str) -> None:
        """Test importing a non-existent document."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={"results": [], "nextPageCursor": None},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            importer = AsyncDocumentImporter(client)

            with pytest.raises(ValueError, match="not found"):
                await importer.import_document("nonexistent")

    @pytest.mark.asyncio
    @respx.mock
    async def test_import_batch(self, api_key: str) -> None:
        """Test importing multiple documents."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "results": [
                            {"id": "doc1", "url": "https://a.com", "title": "Doc 1", "tags": []}
                        ],
                        "nextPageCursor": None,
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "results": [
                            {"id": "doc2", "url": "https://b.com", "title": "Doc 2", "tags": []}
                        ],
                        "nextPageCursor": None,
                    },
                ),
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            importer = AsyncDocumentImporter(client)
            results = await importer.import_batch(["doc1", "doc2"])

        assert len(results) == 2
        assert results[0].success is True
        assert results[0].document is not None
        assert results[0].document.id == "doc1"
        assert results[1].success is True
        assert results[1].document is not None
        assert results[1].document.id == "doc2"

    @pytest.mark.asyncio
    @respx.mock
    async def test_import_batch_with_failure(self, api_key: str) -> None:
        """Test batch import with one failure."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "results": [
                            {"id": "doc1", "url": "https://a.com", "title": "Doc 1", "tags": []}
                        ],
                        "nextPageCursor": None,
                    },
                ),
                httpx.Response(
                    200,
                    json={"results": [], "nextPageCursor": None},  # Not found
                ),
            ]
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            importer = AsyncDocumentImporter(client)
            results = await importer.import_batch(["doc1", "doc_missing"])

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False
        assert results[1].error is not None
        assert "not found" in results[1].error.lower()

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_inbox(self, api_key: str) -> None:
        """Test listing inbox documents."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://a.com", "title": "Inbox 1", "tags": []},
                        {"id": "doc2", "url": "https://b.com", "title": "Inbox 2", "tags": []},
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            importer = AsyncDocumentImporter(client)
            docs = await importer.list_inbox(limit=10)

        assert len(docs) == 2
        assert docs[0].id == "doc1"
        request = route.calls.last.request
        assert "location=new" in str(request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_reading_list(self, api_key: str) -> None:
        """Test listing reading list documents."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://a.com", "title": "Later 1", "tags": []}
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            importer = AsyncDocumentImporter(client)
            docs = await importer.list_reading_list()

        assert len(docs) == 1
        request = route.calls.last.request
        assert "location=later" in str(request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_archive(self, api_key: str) -> None:
        """Test listing archived documents."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://a.com", "title": "Archived", "tags": []}
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            importer = AsyncDocumentImporter(client)
            docs = await importer.list_archive()

        assert len(docs) == 1
        request = route.calls.last.request
        assert "location=archive" in str(request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_updated_since(self, api_key: str) -> None:
        """Test listing documents updated since a timestamp."""
        route = respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {"id": "doc1", "url": "https://a.com", "title": "Updated", "tags": []}
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            importer = AsyncDocumentImporter(client)
            since = datetime(2024, 1, 1)
            docs = await importer.list_updated_since(since)

        assert len(docs) == 1
        request = route.calls.last.request
        assert "updatedAfter" in str(request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_save_url(self, api_key: str) -> None:
        """Test saving a URL."""
        respx.post(f"{READWISE_API_V3_BASE}/save/").mock(
            return_value=httpx.Response(
                200,
                json={"id": "new_doc_id", "url": "https://example.com/article"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            importer = AsyncDocumentImporter(client)
            doc_id = await importer.save_url("https://example.com/article")

        assert doc_id == "new_doc_id"

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_with_limit(self, api_key: str) -> None:
        """Test listing with limit parameter."""
        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "id": f"doc{i}",
                            "url": f"https://{i}.com",
                            "title": f"Doc {i}",
                            "tags": [],
                        }
                        for i in range(10)
                    ],
                    "nextPageCursor": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            importer = AsyncDocumentImporter(client)
            docs = await importer.list_inbox(limit=3)

        assert len(docs) == 3

    @pytest.mark.asyncio
    async def test_importer_options(self, api_key: str) -> None:
        """Test importer configuration options."""
        async with AsyncReadwiseClient(api_key=api_key) as client:
            # Default options
            importer1 = AsyncDocumentImporter(client)
            assert importer1._extract_metadata is True
            assert importer1._clean_html is True

            # Custom options
            importer2 = AsyncDocumentImporter(client, extract_metadata=False, clean_html=False)
            assert importer2._extract_metadata is False
            assert importer2._clean_html is False
