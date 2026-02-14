"""Shared fixtures for workflow tests."""

import httpx
import pytest

from readwise_sdk.client import READWISE_API_V2_BASE, READWISE_API_V3_BASE, ReadwiseClient


@pytest.fixture
def client(api_key: str) -> ReadwiseClient:
    """Create a ReadwiseClient for testing."""
    return ReadwiseClient(api_key=api_key)


def mock_v2_highlights(results: list[dict], *, next_page: str | None = None) -> None:
    """Mock the v2 highlights list endpoint."""
    import respx

    respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
        return_value=httpx.Response(
            200,
            json={"results": results, "next": next_page},
        )
    )


def mock_v2_books(results: list[dict], *, next_page: str | None = None) -> None:
    """Mock the v2 books list endpoint."""
    import respx

    respx.get(f"{READWISE_API_V2_BASE}/books/").mock(
        return_value=httpx.Response(
            200,
            json={"results": results, "next": next_page},
        )
    )


def mock_v3_documents(results: list[dict], *, next_cursor: str | None = None) -> None:
    """Mock the v3 documents list endpoint."""
    import respx

    respx.get(f"{READWISE_API_V3_BASE}/list/").mock(
        return_value=httpx.Response(
            200,
            json={"results": results, "nextPageCursor": next_cursor},
        )
    )


def mock_full_sync(
    *,
    highlights: list[dict] | None = None,
    books: list[dict] | None = None,
    documents: list[dict] | None = None,
) -> None:
    """Mock all three sync endpoints (highlights, books, documents)."""
    mock_v2_highlights(highlights or [])
    mock_v2_books(books or [])
    mock_v3_documents(documents or [])
