"""Tests for DigestBuilder."""

import json
from datetime import UTC, datetime, timedelta

import httpx
import pytest
import respx

from readwise_sdk.client import READWISE_API_V2_BASE, ReadwiseClient
from readwise_sdk.workflows.digest import DigestBuilder, DigestFormat
from tests.workflows.conftest import mock_v2_highlights


class TestDigestBuilder:
    """Tests for DigestBuilder."""

    @respx.mock
    def test_create_daily_digest_markdown(self, client: ReadwiseClient) -> None:
        """Test creating daily digest in markdown format."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test highlight one", "note": "My note", "book_id": 100},
                {"id": 2, "text": "Test highlight two", "book_id": 100},
            ]
        )

        builder = DigestBuilder(client)
        digest = builder.create_daily_digest(output_format=DigestFormat.MARKDOWN)

        assert "# Daily Digest" in digest
        assert "Test highlight one" in digest
        assert "Test highlight two" in digest
        assert "My note" in digest

    @respx.mock
    def test_create_weekly_digest(self, client: ReadwiseClient) -> None:
        """Test creating weekly digest."""
        mock_v2_highlights([{"id": 1, "text": "Weekly highlight"}])

        builder = DigestBuilder(client)
        digest = builder.create_weekly_digest(output_format=DigestFormat.TEXT)

        assert "Weekly Digest" in digest
        assert "Weekly highlight" in digest

    @respx.mock
    def test_create_book_digest(self, client: ReadwiseClient) -> None:
        """Test creating digest for a specific book."""
        respx.get(f"{READWISE_API_V2_BASE}/books/123/").mock(
            return_value=httpx.Response(
                200, json={"id": 123, "title": "My Book", "num_highlights": 2}
            )
        )
        mock_v2_highlights(
            [
                {"id": 1, "text": "Book highlight 1", "book_id": 123},
                {"id": 2, "text": "Book highlight 2", "book_id": 123},
            ]
        )

        builder = DigestBuilder(client)
        digest = builder.create_book_digest(123, output_format=DigestFormat.MARKDOWN)

        assert "My Book" in digest
        assert "Book highlight 1" in digest
        assert "Book highlight 2" in digest

    @respx.mock
    @pytest.mark.parametrize(
        ("output_format", "expected_strings"),
        [
            (DigestFormat.JSON, ["Daily Digest", "JSON highlight"]),
            (DigestFormat.CSV, ["id,text,note", "CSV highlight"]),
        ],
        ids=["json", "csv"],
    )
    def test_digest_structured_formats(
        self,
        client: ReadwiseClient,
        output_format: DigestFormat,
        expected_strings: list[str],
    ) -> None:
        """Test JSON and CSV output formats."""
        text = expected_strings[-1]
        mock_v2_highlights([{"id": 1, "text": text, "note": "Note"}])

        builder = DigestBuilder(client)
        digest = builder.create_daily_digest(output_format=output_format)

        if output_format == DigestFormat.JSON:
            data = json.loads(digest)
            assert data["title"] == "Daily Digest"
            assert data["count"] == 1
            assert data["highlights"][0]["text"] == text
        else:
            for expected in expected_strings:
                assert expected in digest

    @respx.mock
    def test_digest_empty(self, client: ReadwiseClient) -> None:
        """Test digest with no highlights."""
        mock_v2_highlights([])

        builder = DigestBuilder(client)
        digest = builder.create_daily_digest()

        assert "0 highlights" in digest

    @respx.mock
    def test_digest_group_by_date(self, client: ReadwiseClient) -> None:
        """Test grouping highlights by date."""
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)

        mock_v2_highlights(
            [
                {"id": 1, "text": "Today highlight", "highlighted_at": now.isoformat()},
                {"id": 2, "text": "Yesterday highlight", "highlighted_at": yesterday.isoformat()},
            ]
        )

        builder = DigestBuilder(client)
        digest = builder.create_custom_digest(
            output_format=DigestFormat.MARKDOWN,
            group_by_date=True,
            group_by_book=False,
        )

        assert "Today highlight" in digest
        assert "Yesterday highlight" in digest

    @respx.mock
    def test_text_format_group_by_date(self, client: ReadwiseClient) -> None:
        """Test text output format with date grouping."""
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)

        mock_v2_highlights(
            [
                {
                    "id": 1,
                    "text": "Today text highlight",
                    "note": "A note",
                    "highlighted_at": now.isoformat(),
                },
                {
                    "id": 2,
                    "text": "Yesterday text highlight",
                    "highlighted_at": yesterday.isoformat(),
                },
            ]
        )

        builder = DigestBuilder(client)
        digest = builder.create_custom_digest(
            output_format=DigestFormat.TEXT,
            group_by_date=True,
            group_by_book=False,
        )

        assert "Custom Digest" in digest
        assert "Today text highlight" in digest
        assert "Yesterday text highlight" in digest
        assert "Note: A note" in digest
        assert now.strftime("%Y-%m-%d") in digest
        assert yesterday.strftime("%Y-%m-%d") in digest

    @respx.mock
    def test_text_format_ungrouped(self, client: ReadwiseClient) -> None:
        """Test text output format without any grouping."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Ungrouped highlight one", "note": "My note"},
                {"id": 2, "text": "Ungrouped highlight two"},
            ]
        )

        builder = DigestBuilder(client)
        digest = builder.create_custom_digest(
            output_format=DigestFormat.TEXT,
            group_by_book=False,
            group_by_date=False,
        )

        assert "Custom Digest" in digest
        assert "Ungrouped highlight one" in digest
        assert "Ungrouped highlight two" in digest
        assert "Note: My note" in digest

    @respx.mock
    def test_markdown_with_location_and_tags(self, client: ReadwiseClient) -> None:
        """Test markdown format includes highlight location and tags metadata."""
        mock_v2_highlights(
            [
                {
                    "id": 1,
                    "text": "Highlight with metadata",
                    "location": 42,
                    "note": "Important note",
                    "book_id": 100,
                    "tags": [{"id": 1, "name": "science"}, {"id": 2, "name": "review"}],
                },
            ]
        )

        builder = DigestBuilder(client)
        digest = builder.create_custom_digest(
            output_format=DigestFormat.MARKDOWN,
            group_by_book=False,
        )

        assert "Highlight with metadata" in digest
        assert "Location: 42" in digest
        assert "Note: Important note" in digest
        assert "Tags: science, review" in digest
        assert "Book ID: 100" in digest

    @respx.mock
    def test_group_by_date_unknown(self, client: ReadwiseClient) -> None:
        """Test grouping by date when highlights have no highlighted_at timestamp."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "No timestamp highlight"},
                {"id": 2, "text": "Also no timestamp"},
            ]
        )

        builder = DigestBuilder(client)
        digest = builder.create_custom_digest(
            output_format=DigestFormat.MARKDOWN,
            group_by_date=True,
            group_by_book=False,
        )

        assert "Unknown Date" in digest
        assert "No timestamp highlight" in digest
        assert "Also no timestamp" in digest
