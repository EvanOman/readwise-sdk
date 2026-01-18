"""Tests for AsyncReadwiseClient."""

import httpx
import pytest
import respx

from readwise_sdk import AsyncReadwiseClient
from readwise_sdk.client import READWISE_API_V2_BASE
from readwise_sdk.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ReadwiseError,
)


class TestAsyncClientInit:
    """Tests for async client initialization."""

    def test_client_with_api_key(self, api_key: str) -> None:
        """Test creating client with explicit API key."""
        client = AsyncReadwiseClient(api_key=api_key)
        assert client.api_key == api_key

    def test_client_requires_api_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that client raises error without API key."""
        monkeypatch.delenv("READWISE_API_KEY", raising=False)
        with pytest.raises(AuthenticationError):
            AsyncReadwiseClient()

    def test_client_reads_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that client reads READWISE_API_KEY from environment."""
        monkeypatch.setenv("READWISE_API_KEY", "env_test_key")
        client = AsyncReadwiseClient()
        assert client.api_key == "env_test_key"

    def test_default_config(self, api_key: str) -> None:
        """Test default configuration values."""
        client = AsyncReadwiseClient(api_key=api_key)
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.retry_backoff == 0.5

    def test_custom_config(self, api_key: str) -> None:
        """Test custom configuration values."""
        client = AsyncReadwiseClient(
            api_key=api_key,
            timeout=60.0,
            max_retries=5,
            retry_backoff=1.0,
        )
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.retry_backoff == 1.0


class TestAsyncClientContextManager:
    """Tests for async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self, api_key: str) -> None:
        """Test async context manager protocol."""
        async with AsyncReadwiseClient(api_key=api_key) as client:
            # Client is lazily initialized, so access it to trigger creation
            _ = client.client
            assert client._client is not None
        # Client should be closed after exiting context
        assert client._client is None

    @pytest.mark.asyncio
    async def test_explicit_close(self, api_key: str) -> None:
        """Test explicit close method."""
        client = AsyncReadwiseClient(api_key=api_key)
        # Access client property to initialize it
        _ = client.client
        assert client._client is not None
        await client.close()
        assert client._client is None


class TestAsyncClientProperties:
    """Tests for async client properties."""

    def test_v2_property(self, api_key: str) -> None:
        """Test v2 property returns async v2 client."""
        client = AsyncReadwiseClient(api_key=api_key)
        v2 = client.v2
        assert v2 is not None
        # Should be cached
        assert client.v2 is v2

    def test_v3_property(self, api_key: str) -> None:
        """Test v3 property returns async v3 client."""
        client = AsyncReadwiseClient(api_key=api_key)
        v3 = client.v3
        assert v3 is not None
        # Should be cached
        assert client.v3 is v3


class TestAsyncValidateToken:
    """Tests for token validation."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_validate_token_success(self, api_key: str) -> None:
        """Test successful token validation."""
        respx.get(f"{READWISE_API_V2_BASE}/auth/").mock(return_value=httpx.Response(204))

        async with AsyncReadwiseClient(api_key=api_key) as client:
            result = await client.validate_token()
            assert result is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_validate_token_failure(self, api_key: str) -> None:
        """Test failed token validation."""
        respx.get(f"{READWISE_API_V2_BASE}/auth/").mock(
            return_value=httpx.Response(401, text="Invalid token")
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            with pytest.raises(AuthenticationError):
                await client.validate_token()


class TestAsyncErrorHandling:
    """Tests for async error handling."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_handle_404(self, api_key: str) -> None:
        """Test 404 error handling."""
        respx.get(f"{READWISE_API_V2_BASE}/test/").mock(
            return_value=httpx.Response(404, text="Not found")
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            with pytest.raises(NotFoundError):
                await client.get(f"{READWISE_API_V2_BASE}/test/")

    @respx.mock
    @pytest.mark.asyncio
    async def test_handle_429_with_retry_after(self, api_key: str) -> None:
        """Test rate limit error with Retry-After header."""
        respx.get(f"{READWISE_API_V2_BASE}/test/").mock(
            return_value=httpx.Response(
                429,
                text="Rate limited",
                headers={"Retry-After": "30"},
            )
        )

        async with AsyncReadwiseClient(api_key=api_key, max_retries=0) as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.get(f"{READWISE_API_V2_BASE}/test/")
            assert exc_info.value.retry_after == 30


class TestAsyncPagination:
    """Tests for async pagination."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_single_page(self, api_key: str) -> None:
        """Test pagination with single page."""
        respx.get(f"{READWISE_API_V2_BASE}/items/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "results": [{"id": 1}, {"id": 2}],
                    "next": None,
                },
            )
        )

        async with AsyncReadwiseClient(api_key=api_key) as client:
            items = []
            async for item in client.paginate(f"{READWISE_API_V2_BASE}/items/"):
                items.append(item)

            assert len(items) == 2
            assert items[0]["id"] == 1
            assert items[1]["id"] == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_multiple_pages(self, api_key: str) -> None:
        """Test pagination with multiple pages."""
        # Use side_effect to return different responses for sequential calls
        route = respx.get(url__startswith=f"{READWISE_API_V2_BASE}/items/")
        route.side_effect = [
            httpx.Response(
                200,
                json={
                    "results": [{"id": 1}],
                    "next": f"{READWISE_API_V2_BASE}/items/?page=2",
                },
            ),
            httpx.Response(
                200,
                json={
                    "results": [{"id": 2}],
                    "next": None,
                },
            ),
        ]

        async with AsyncReadwiseClient(api_key=api_key) as client:
            items = []
            async for item in client.paginate(f"{READWISE_API_V2_BASE}/items/"):
                items.append(item)

            assert len(items) == 2
            assert route.call_count == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_pagination_with_cursor(self, api_key: str) -> None:
        """Test pagination with cursor-based pagination."""
        route = respx.get(url__startswith=f"{READWISE_API_V2_BASE}/items/")
        route.side_effect = [
            httpx.Response(
                200,
                json={
                    "results": [{"id": 1}],
                    "nextPageCursor": "abc123",
                },
            ),
            httpx.Response(
                200,
                json={
                    "results": [{"id": 2}],
                    "nextPageCursor": None,
                },
            ),
        ]

        async with AsyncReadwiseClient(api_key=api_key) as client:
            items = []
            async for item in client.paginate(
                f"{READWISE_API_V2_BASE}/items/",
                cursor_key="nextPageCursor",
            ):
                items.append(item)

            assert len(items) == 2
            assert route.call_count == 2


class TestAsyncRetry:
    """Tests for async retry logic."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self, api_key: str) -> None:
        """Test retry on connection error."""
        route = respx.get(f"{READWISE_API_V2_BASE}/test/")
        route.side_effect = [
            httpx.ConnectError("Connection failed"),
            httpx.Response(200, json={"status": "ok"}),
        ]

        async with AsyncReadwiseClient(
            api_key=api_key, max_retries=1, retry_backoff=0.01
        ) as client:
            response = await client.get(f"{READWISE_API_V2_BASE}/test/")
            assert response.status_code == 200

    @respx.mock
    @pytest.mark.asyncio
    async def test_retry_exhausted(self, api_key: str) -> None:
        """Test error when retries exhausted."""
        respx.get(f"{READWISE_API_V2_BASE}/test/").mock(
            side_effect=httpx.ConnectError("Connection failed")
        )

        async with AsyncReadwiseClient(
            api_key=api_key, max_retries=2, retry_backoff=0.01
        ) as client:
            with pytest.raises(ReadwiseError) as exc_info:
                await client.get(f"{READWISE_API_V2_BASE}/test/")
            assert "failed after 3 attempts" in str(exc_info.value)
