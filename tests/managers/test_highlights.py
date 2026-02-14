"""Tests for HighlightManager."""

import httpx
import pytest
import respx

from readwise_sdk.client import READWISE_API_V2_BASE, ReadwiseClient
from readwise_sdk.managers.highlights import HighlightManager

V2_HIGHLIGHTS = f"{READWISE_API_V2_BASE}/highlights/"


def _make_manager(api_key: str) -> HighlightManager:
    return HighlightManager(ReadwiseClient(api_key=api_key))


def _mock_highlights_response(results: list[dict], *, next_url: str | None = None) -> None:
    respx.get(V2_HIGHLIGHTS).mock(
        return_value=httpx.Response(200, json={"results": results, "next": next_url})
    )


class TestHighlightManager:
    """Tests for HighlightManager."""

    @respx.mock
    def test_get_all_highlights(self, api_key: str) -> None:
        """Test getting all highlights."""
        _mock_highlights_response([{"id": 1, "text": "First"}, {"id": 2, "text": "Second"}])

        highlights = _make_manager(api_key).get_all_highlights()

        assert len(highlights) == 2
        assert highlights[0].text == "First"

    @respx.mock
    def test_get_highlights_by_book(self, api_key: str) -> None:
        """Test getting highlights for a specific book."""
        route = respx.get(V2_HIGHLIGHTS).mock(
            return_value=httpx.Response(
                200, json={"results": [{"id": 1, "text": "Test"}], "next": None}
            )
        )

        _make_manager(api_key).get_highlights_by_book(123)

        assert "book_id=123" in str(route.calls.last.request.url)

    @respx.mock
    def test_get_highlights_with_notes(self, api_key: str) -> None:
        """Test getting highlights with notes."""
        _mock_highlights_response(
            [
                {"id": 1, "text": "No note", "note": None},
                {"id": 2, "text": "Has note", "note": "My note"},
            ]
        )

        highlights = _make_manager(api_key).get_highlights_with_notes()

        assert len(highlights) == 1
        assert highlights[0].id == 2

    @respx.mock
    def test_search_highlights(self, api_key: str) -> None:
        """Test searching highlights."""
        _mock_highlights_response(
            [
                {"id": 1, "text": "Python programming"},
                {"id": 2, "text": "JavaScript basics"},
            ]
        )

        results = _make_manager(api_key).search_highlights("python")

        assert len(results) == 1
        assert "Python" in results[0].text

    @respx.mock
    def test_bulk_tag(self, api_key: str) -> None:
        """Test bulk tagging highlights."""
        respx.post(url__startswith=V2_HIGHLIGHTS).mock(
            return_value=httpx.Response(200, json={"id": 1, "name": "test-tag"})
        )

        results = _make_manager(api_key).bulk_tag([1, 2], "test-tag")

        assert results == {1: True, 2: True}

    @respx.mock
    def test_create_highlight(self, api_key: str) -> None:
        """Test creating a single highlight."""
        respx.post(V2_HIGHLIGHTS).mock(
            return_value=httpx.Response(200, json=[{"modified_highlights": [999]}])
        )

        highlight_id = _make_manager(api_key).create_highlight(
            text="New highlight text", title="My Book", author="Author"
        )

        assert highlight_id == 999

    @respx.mock
    def test_get_highlight_count(self, api_key: str) -> None:
        """Test getting highlight count."""
        _mock_highlights_response([{"id": 1, "text": "A"}, {"id": 2, "text": "B"}])

        assert _make_manager(api_key).get_highlight_count() == 2

    @respx.mock
    @pytest.mark.parametrize(
        ("kwargs", "description"),
        [
            ({"days": 7}, "days"),
            ({"hours": 24}, "hours"),
        ],
    )
    def test_get_highlights_since(self, api_key: str, kwargs: dict, description: str) -> None:
        """Test getting highlights since N days/hours ago."""
        route = respx.get(V2_HIGHLIGHTS).mock(
            return_value=httpx.Response(
                200, json={"results": [{"id": 1, "text": "Recent"}], "next": None}
            )
        )

        highlights = _make_manager(api_key).get_highlights_since(**kwargs)

        assert len(highlights) == 1
        assert "updated__gt" in str(route.calls.last.request.url)

    def test_get_highlights_since_error(self, api_key: str) -> None:
        """Test that get_highlights_since raises when no time arg is given."""
        with pytest.raises(ValueError, match="Must specify days, hours, or since"):
            _make_manager(api_key).get_highlights_since()

    @respx.mock
    def test_filter_highlights(self, api_key: str) -> None:
        """Test filtering highlights with a predicate."""
        _mock_highlights_response(
            [
                {"id": 1, "text": "Short"},
                {"id": 2, "text": "This is a much longer highlight text"},
            ]
        )

        results = list(_make_manager(api_key).filter_highlights(lambda h: len(h.text) > 10))

        assert len(results) == 1
        assert results[0].id == 2

    @respx.mock
    def test_bulk_untag_success(self, api_key: str) -> None:
        """Test bulk untagging highlights - success path."""
        for hid, tag_id in [(1, 10), (2, 20)]:
            respx.get(f"{V2_HIGHLIGHTS}{hid}/tags/").mock(
                return_value=httpx.Response(
                    200, json={"results": [{"id": tag_id, "name": "test-tag"}], "next": None}
                )
            )
            respx.delete(f"{V2_HIGHLIGHTS}{hid}/tags/{tag_id}/").mock(
                return_value=httpx.Response(204)
            )

        results = _make_manager(api_key).bulk_untag([1, 2], "test-tag")

        assert results == {1: True, 2: True}

    @respx.mock
    def test_bulk_untag_no_matching_tag(self, api_key: str) -> None:
        """Test bulk untagging when tag does not exist on highlight."""
        respx.get(f"{V2_HIGHLIGHTS}1/tags/").mock(
            return_value=httpx.Response(
                200, json={"results": [{"id": 10, "name": "other-tag"}], "next": None}
            )
        )

        results = _make_manager(api_key).bulk_untag([1], "test-tag")

        assert results[1] is True

    @respx.mock
    def test_bulk_untag_exception_path(self, api_key: str) -> None:
        """Test bulk untagging when API call raises an exception."""
        respx.get(f"{V2_HIGHLIGHTS}1/tags/").mock(return_value=httpx.Response(500))

        assert _make_manager(api_key).bulk_untag([1], "test-tag") == {1: False}

    @respx.mock
    def test_bulk_tag_exception_path(self, api_key: str) -> None:
        """Test bulk tagging when API call raises an exception."""
        respx.post(url__startswith=V2_HIGHLIGHTS).mock(return_value=httpx.Response(500))

        assert _make_manager(api_key).bulk_tag([1, 2], "test-tag") == {1: False, 2: False}
