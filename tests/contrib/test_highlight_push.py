"""Tests for HighlightPusher."""

from datetime import datetime
from typing import Any

import httpx
import respx

from readwise_sdk.client import READWISE_API_V2_BASE, ReadwiseClient
from readwise_sdk.contrib.highlight_push import (
    MAX_AUTHOR_LENGTH,
    MAX_NOTE_LENGTH,
    MAX_TEXT_LENGTH,
    MAX_TITLE_LENGTH,
    DeleteResult,
    FieldTruncation,
    HighlightPusher,
    PushResult,
    SimpleHighlight,
    TruncationInfo,
    UpdateResult,
)
from readwise_sdk.v2.models import BookCategory


def _highlight_response(
    highlight_id: int,
    text: str = "text",
    note: str | None = None,
    book_id: int = 456,
) -> dict[str, Any]:
    """Build a full highlight response dict for mock returns."""
    return {
        "id": highlight_id,
        "text": text,
        "note": note,
        "location": None,
        "location_type": None,
        "url": None,
        "color": None,
        "highlighted_at": None,
        "created_at": None,
        "updated_at": None,
        "book_id": book_id,
        "tags": [],
    }


class TestSimpleHighlight:
    """Tests for SimpleHighlight dataclass."""

    def test_minimal_highlight(self) -> None:
        """Test creating a minimal highlight."""
        h = SimpleHighlight(text="Test text", title="Test Title")
        assert h.text == "Test text"
        assert h.title == "Test Title"
        assert h.author is None
        assert h.category is None

    def test_full_highlight(self) -> None:
        """Test creating a full highlight with all fields."""
        now = datetime.now()
        h = SimpleHighlight(
            text="Test text",
            title="Test Title",
            author="John Doe",
            source_url="https://example.com",
            source_type="custom",
            category=BookCategory.BOOKS,
            note="My note",
            location=42,
            location_type="page",
            highlighted_at=now,
            tags=["tag1", "tag2"],
        )
        assert h.text == "Test text"
        assert h.author == "John Doe"
        assert h.category == BookCategory.BOOKS
        assert h.highlighted_at == now
        assert h.tags == ["tag1", "tag2"]


class TestPushResult:
    """Tests for PushResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful push result."""
        result = PushResult(success=True, highlight_id=123, book_id=456)
        assert result.success is True
        assert result.highlight_id == 123
        assert result.book_id == 456
        assert result.error is None
        assert result.was_truncated is False
        assert result.truncation_info is None

    def test_failure_result(self) -> None:
        """Test failed push result."""
        result = PushResult(success=False, error="API error")
        assert result.success is False
        assert result.highlight_id is None
        assert result.error == "API error"
        assert result.truncation_info is None


class TestFieldTruncation:
    """Tests for FieldTruncation dataclass."""

    def test_chars_removed(self) -> None:
        """Test chars_removed property."""
        ft = FieldTruncation(field_name="text", original_length=9000, truncated_length=8191)
        assert ft.chars_removed == 809

    def test_no_chars_removed(self) -> None:
        """Test chars_removed when lengths are equal."""
        ft = FieldTruncation(field_name="text", original_length=100, truncated_length=100)
        assert ft.chars_removed == 0


class TestTruncationInfo:
    """Tests for TruncationInfo dataclass."""

    def test_empty_fields(self) -> None:
        """Test TruncationInfo with no fields."""
        info = TruncationInfo()
        assert info.fields == []
        assert info.truncated_field_names == []

    def test_truncated_field_names(self) -> None:
        """Test truncated_field_names property."""
        info = TruncationInfo(
            fields=[
                FieldTruncation(field_name="text", original_length=9000, truncated_length=8191),
                FieldTruncation(field_name="title", original_length=600, truncated_length=511),
            ]
        )
        assert info.truncated_field_names == ["text", "title"]

    def test_single_field(self) -> None:
        """Test TruncationInfo with a single truncated field."""
        info = TruncationInfo(
            fields=[
                FieldTruncation(field_name="note", original_length=10000, truncated_length=8191),
            ]
        )
        assert len(info.fields) == 1
        assert info.truncated_field_names == ["note"]
        assert info.fields[0].chars_removed == 1809


class TestHighlightPusher:
    """Tests for HighlightPusher."""

    @respx.mock
    def test_push_single_highlight(self, api_key: str) -> None:
        """Test pushing a single highlight."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [123]}],
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        result = pusher.push(
            text="Test highlight",
            title="Test Book",
            author="Test Author",
        )

        assert result.success is True
        assert result.highlight_id == 123
        assert result.was_truncated is False
        assert result.truncation_info is None

    @respx.mock
    def test_push_with_all_fields(self, api_key: str) -> None:
        """Test pushing a highlight with all fields."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [456]}],
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        result = pusher.push(
            text="Test highlight",
            title="Test Book",
            author="Test Author",
            source_url="https://example.com",
            source_type="article",
            category=BookCategory.ARTICLES,
            note="My note",
            location=10,
            highlighted_at=datetime(2024, 1, 1),
            tags=["tag1"],
        )

        assert result.success is True
        assert result.highlight_id == 456

    @respx.mock
    def test_push_highlight_object(self, api_key: str) -> None:
        """Test pushing a SimpleHighlight object."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [789]}],
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        highlight = SimpleHighlight(text="Object highlight", title="Object Book")
        result = pusher.push_highlight(highlight)

        assert result.success is True
        assert result.highlight_id == 789
        assert result.original is highlight

    @respx.mock
    def test_push_batch(self, api_key: str) -> None:
        """Test pushing multiple highlights."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [1, 2, 3]}],
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        highlights = [
            SimpleHighlight(text="First", title="Book 1"),
            SimpleHighlight(text="Second", title="Book 2"),
            SimpleHighlight(text="Third", title="Book 3"),
        ]
        results = pusher.push_batch(highlights)

        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].highlight_id == 1
        assert results[1].highlight_id == 2
        assert results[2].highlight_id == 3

    def test_push_batch_empty(self, api_key: str) -> None:
        """Test pushing empty batch."""
        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        results = pusher.push_batch([])
        assert results == []

    @respx.mock
    def test_push_batch_api_failure(self, api_key: str) -> None:
        """Test batch push with API failure."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        highlights = [
            SimpleHighlight(text="First", title="Book 1"),
            SimpleHighlight(text="Second", title="Book 2"),
        ]
        results = pusher.push_batch(highlights)

        assert len(results) == 2
        assert all(not r.success for r in results)
        assert all(r.error is not None for r in results)

    @respx.mock
    def test_push_with_truncation(self, api_key: str) -> None:
        """Test pushing with auto-truncation of long fields."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [999]}],
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client, auto_truncate=True)

        # Create text longer than MAX_TEXT_LENGTH
        long_text = "x" * (MAX_TEXT_LENGTH + 100)
        result = pusher.push(text=long_text, title="Test")

        assert result.success is True
        assert result.was_truncated is True
        assert result.truncation_info is not None
        assert len(result.truncation_info.fields) == 1
        assert result.truncation_info.fields[0].field_name == "text"
        assert result.truncation_info.fields[0].original_length == MAX_TEXT_LENGTH + 100
        assert result.truncation_info.fields[0].truncated_length == MAX_TEXT_LENGTH
        assert result.truncation_info.fields[0].chars_removed == 100
        assert result.truncation_info.truncated_field_names == ["text"]

    @respx.mock
    def test_push_truncation_all_fields(self, api_key: str) -> None:
        """Test truncation of all field types."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [111]}],
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client, auto_truncate=True)

        result = pusher.push(
            text="x" * (MAX_TEXT_LENGTH + 10),
            title="y" * (MAX_TITLE_LENGTH + 10),
            author="z" * (MAX_AUTHOR_LENGTH + 10),
            note="n" * (MAX_NOTE_LENGTH + 10),
        )

        assert result.success is True
        assert result.was_truncated is True
        assert result.truncation_info is not None
        assert len(result.truncation_info.fields) == 4
        assert result.truncation_info.truncated_field_names == [
            "text",
            "note",
            "title",
            "author",
        ]
        # Verify each field has correct lengths
        by_name = {f.field_name: f for f in result.truncation_info.fields}
        assert by_name["text"].original_length == MAX_TEXT_LENGTH + 10
        assert by_name["text"].truncated_length == MAX_TEXT_LENGTH
        assert by_name["note"].original_length == MAX_NOTE_LENGTH + 10
        assert by_name["note"].truncated_length == MAX_NOTE_LENGTH
        assert by_name["title"].original_length == MAX_TITLE_LENGTH + 10
        assert by_name["title"].truncated_length == MAX_TITLE_LENGTH
        assert by_name["author"].original_length == MAX_AUTHOR_LENGTH + 10
        assert by_name["author"].truncated_length == MAX_AUTHOR_LENGTH

    @respx.mock
    def test_push_none_text_with_auto_truncate(self, api_key: str) -> None:
        """Test pushing with text=None and auto_truncate enabled."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [555]}],
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client, auto_truncate=True)

        # Create a SimpleHighlight with text set to None via direct construction
        # (bypassing the push() method which requires text as str)
        highlight = SimpleHighlight(text=None, title="Test")  # type: ignore[arg-type]
        results = pusher.push_batch([highlight])

        assert len(results) == 1
        assert results[0].success is True
        assert results[0].highlight_id == 555
        assert results[0].was_truncated is False

    @respx.mock
    def test_update_note_truncation(self, api_key: str) -> None:
        """Test updating a highlight with a note exceeding MAX_NOTE_LENGTH."""
        respx.patch(f"{READWISE_API_V2_BASE}/highlights/123/").mock(
            return_value=httpx.Response(
                200,
                json=_highlight_response(123, text="Original text", note="n" * MAX_NOTE_LENGTH),
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client, auto_truncate=True)

        long_note = "n" * (MAX_NOTE_LENGTH + 200)
        result = pusher.update(highlight_id=123, note=long_note)

        assert result.success is True
        assert result.was_truncated is True
        assert result.truncation_info is not None
        assert len(result.truncation_info.fields) == 1
        assert result.truncation_info.fields[0].field_name == "note"
        assert result.truncation_info.fields[0].original_length == MAX_NOTE_LENGTH + 200
        assert result.truncation_info.fields[0].truncated_length == MAX_NOTE_LENGTH

    @respx.mock
    def test_push_no_truncation_when_disabled(self, api_key: str) -> None:
        """Test that truncation is not applied when disabled."""
        route = respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [222]}],
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client, auto_truncate=False)

        # Text within limits - should not truncate
        short_text = "Short text"
        result = pusher.push(text=short_text, title="Test")

        assert result.success is True
        assert result.was_truncated is False
        assert result.truncation_info is None
        # Verify the request was made
        assert route.called

    def test_truncate_field_none(self) -> None:
        """Test truncating None value."""
        from readwise_sdk._utils import truncate_string

        value, was_truncated = truncate_string(None, 100)
        assert value is None
        assert was_truncated is False

    def test_truncate_field_short(self) -> None:
        """Test truncating short value (no truncation needed)."""
        from readwise_sdk._utils import truncate_string

        value, was_truncated = truncate_string("short", 100)
        assert value == "short"
        assert was_truncated is False

    def test_truncate_field_long(self) -> None:
        """Test truncating long value."""
        from readwise_sdk._utils import truncate_string

        long_value = "x" * 200
        value, was_truncated = truncate_string(long_value, 100)
        assert value is not None
        assert len(value) == 100
        assert value.endswith("...")
        assert was_truncated is True

    @respx.mock
    def test_validate_token(self, api_key: str) -> None:
        """Test token validation."""
        respx.get(f"{READWISE_API_V2_BASE}/auth/").mock(return_value=httpx.Response(204))

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        assert pusher.validate_token() is True

    @respx.mock
    def test_push_partial_api_result(self, api_key: str) -> None:
        """Test when API returns fewer results than expected."""
        respx.post(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(
                200,
                json=[{"modified_highlights": [1]}],  # Only 1 result for 2 highlights
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        highlights = [
            SimpleHighlight(text="First", title="Book 1"),
            SimpleHighlight(text="Second", title="Book 2"),
        ]
        results = pusher.push_batch(highlights)

        assert len(results) == 2
        assert results[0].success is True
        assert results[0].highlight_id == 1
        assert results[1].success is False
        assert results[1].error is not None
        assert "No API result returned" in results[1].error


class TestUpdateResult:
    """Tests for UpdateResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful update result."""
        result = UpdateResult(success=True, highlight_id=123)
        assert result.success is True
        assert result.highlight_id == 123
        assert result.error is None
        assert result.was_truncated is False
        assert result.truncation_info is None

    def test_failure_result(self) -> None:
        """Test failed update result."""
        result = UpdateResult(success=False, highlight_id=123, error="API error")
        assert result.success is False
        assert result.highlight_id == 123
        assert result.error == "API error"
        assert result.truncation_info is None


class TestDeleteResult:
    """Tests for DeleteResult dataclass."""

    def test_success_result(self) -> None:
        """Test successful delete result."""
        result = DeleteResult(success=True, highlight_id=123)
        assert result.success is True
        assert result.highlight_id == 123
        assert result.error is None

    def test_failure_result(self) -> None:
        """Test failed delete result."""
        result = DeleteResult(success=False, highlight_id=123, error="Not found")
        assert result.success is False
        assert result.highlight_id == 123
        assert result.error == "Not found"


class TestHighlightPusherUpdate:
    """Tests for HighlightPusher update methods."""

    @respx.mock
    def test_update_single_highlight(self, api_key: str) -> None:
        """Test updating a single highlight."""
        respx.patch(f"{READWISE_API_V2_BASE}/highlights/123/").mock(
            return_value=httpx.Response(
                200,
                json=_highlight_response(123, text="Updated text", note="Updated note"),
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        result = pusher.update(
            highlight_id=123,
            text="Updated text",
            note="Updated note",
        )

        assert result.success is True
        assert result.highlight_id == 123
        assert result.highlight is not None
        assert result.highlight.text == "Updated text"
        assert result.was_truncated is False

    @respx.mock
    def test_update_with_truncation(self, api_key: str) -> None:
        """Test updating with auto-truncation of long text."""
        respx.patch(f"{READWISE_API_V2_BASE}/highlights/123/").mock(
            return_value=httpx.Response(
                200,
                json=_highlight_response(123, text="x" * MAX_TEXT_LENGTH),
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client, auto_truncate=True)

        long_text = "x" * (MAX_TEXT_LENGTH + 100)
        result = pusher.update(highlight_id=123, text=long_text)

        assert result.success is True
        assert result.was_truncated is True
        assert result.truncation_info is not None
        assert len(result.truncation_info.fields) == 1
        assert result.truncation_info.fields[0].field_name == "text"
        assert result.truncation_info.fields[0].original_length == MAX_TEXT_LENGTH + 100
        assert result.truncation_info.fields[0].truncated_length == MAX_TEXT_LENGTH

    @respx.mock
    def test_update_batch(self, api_key: str) -> None:
        """Test updating multiple highlights."""
        respx.patch(f"{READWISE_API_V2_BASE}/highlights/1/").mock(
            return_value=httpx.Response(
                200,
                json=_highlight_response(1, text="Updated 1", book_id=100),
            )
        )
        respx.patch(f"{READWISE_API_V2_BASE}/highlights/2/").mock(
            return_value=httpx.Response(
                200,
                json=_highlight_response(2, text="Updated 2", book_id=200),
            )
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        results = pusher.update_batch(
            [
                (1, "Updated 1", None, None, None),
                (2, "Updated 2", None, None, None),
            ]
        )

        assert len(results) == 2
        assert all(r.success for r in results)
        assert results[0].highlight_id == 1
        assert results[1].highlight_id == 2

    @respx.mock
    def test_update_failure(self, api_key: str) -> None:
        """Test update with API failure."""
        respx.patch(f"{READWISE_API_V2_BASE}/highlights/999/").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        result = pusher.update(highlight_id=999, text="New text")

        assert result.success is False
        assert result.highlight_id == 999
        assert result.error is not None


class TestHighlightPusherDelete:
    """Tests for HighlightPusher delete methods."""

    @respx.mock
    def test_delete_single_highlight(self, api_key: str) -> None:
        """Test deleting a single highlight."""
        respx.delete(f"{READWISE_API_V2_BASE}/highlights/123/").mock(
            return_value=httpx.Response(204)
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        result = pusher.delete(highlight_id=123)

        assert result.success is True
        assert result.highlight_id == 123
        assert result.error is None

    @respx.mock
    def test_delete_batch(self, api_key: str) -> None:
        """Test deleting multiple highlights."""
        respx.delete(f"{READWISE_API_V2_BASE}/highlights/1/").mock(return_value=httpx.Response(204))
        respx.delete(f"{READWISE_API_V2_BASE}/highlights/2/").mock(return_value=httpx.Response(204))
        respx.delete(f"{READWISE_API_V2_BASE}/highlights/3/").mock(return_value=httpx.Response(204))

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        results = pusher.delete_batch([1, 2, 3])

        assert len(results) == 3
        assert all(r.success for r in results)
        assert results[0].highlight_id == 1
        assert results[1].highlight_id == 2
        assert results[2].highlight_id == 3

    @respx.mock
    def test_delete_failure(self, api_key: str) -> None:
        """Test delete with API failure."""
        respx.delete(f"{READWISE_API_V2_BASE}/highlights/999/").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        result = pusher.delete(highlight_id=999)

        assert result.success is False
        assert result.highlight_id == 999
        assert result.error is not None

    @respx.mock
    def test_delete_batch_partial_failure(self, api_key: str) -> None:
        """Test batch delete with some failures."""
        respx.delete(f"{READWISE_API_V2_BASE}/highlights/1/").mock(return_value=httpx.Response(204))
        respx.delete(f"{READWISE_API_V2_BASE}/highlights/2/").mock(
            return_value=httpx.Response(404, json={"detail": "Not found"})
        )
        respx.delete(f"{READWISE_API_V2_BASE}/highlights/3/").mock(return_value=httpx.Response(204))

        client = ReadwiseClient(api_key=api_key)
        pusher = HighlightPusher(client)

        results = pusher.delete_batch([1, 2, 3])

        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is False
        assert results[1].error is not None
        assert results[2].success is True
