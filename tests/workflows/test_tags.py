"""Tests for TagWorkflow."""

import httpx
import pytest
import respx

from readwise_sdk.client import READWISE_API_V2_BASE, ReadwiseClient
from readwise_sdk.v2.models import Highlight
from readwise_sdk.workflows.tags import TagPattern, TagWorkflow
from tests.workflows.conftest import mock_v2_highlights


class TestTagPattern:
    """Tests for TagPattern."""

    @pytest.mark.parametrize(
        ("pattern", "tag", "text", "note", "kwargs", "expected"),
        [
            ("python", "programming", "I love Python programming", None, {}, True),
            ("rust", "programming", "I love Python programming", None, {}, False),
            (
                "important",
                "review",
                "Some text",
                "This is important!",
                {"match_in_text": False},
                True,
            ),
        ],
        ids=["matches_text", "no_match", "matches_note"],
    )
    def test_pattern_matching(
        self,
        pattern: str,
        tag: str,
        text: str,
        note: str | None,
        kwargs: dict,
        expected: bool,
    ) -> None:
        """Test pattern matching against highlight text and notes."""
        tag_pattern = TagPattern(pattern=pattern, tag=tag, **kwargs)
        highlight = Highlight(id=1, text=text, note=note)
        assert tag_pattern.matches(highlight) is expected

    def test_case_sensitive(self) -> None:
        """Test case-sensitive matching."""
        pattern = TagPattern(pattern=r"Python", tag="python", case_sensitive=True)
        assert pattern.matches(Highlight(id=1, text="I love Python")) is True
        assert pattern.matches(Highlight(id=2, text="I love python")) is False


class TestTagWorkflow:
    """Tests for TagWorkflow."""

    @respx.mock
    def test_auto_tag_highlights_dry_run(self, client: ReadwiseClient) -> None:
        """Test auto-tagging in dry run mode."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Python is great", "tags": []},
                {"id": 2, "text": "JavaScript is also good", "tags": []},
            ]
        )

        workflow = TagWorkflow(client)
        patterns = [
            TagPattern(pattern=r"python", tag="programming-python"),
            TagPattern(pattern=r"javascript", tag="programming-js"),
        ]
        results = workflow.auto_tag_highlights(patterns, dry_run=True)

        assert results[1] == ["programming-python"]
        assert results[2] == ["programming-js"]

    @respx.mock
    def test_auto_tag_skips_already_tagged(self, client: ReadwiseClient) -> None:
        """Test that auto-tagging skips already tagged highlights."""
        mock_v2_highlights(
            [
                {
                    "id": 1,
                    "text": "Python is great",
                    "tags": [{"id": 10, "name": "programming-python"}],
                },
            ]
        )

        workflow = TagWorkflow(client)
        patterns = [TagPattern(pattern=r"python", tag="programming-python")]
        results = workflow.auto_tag_highlights(patterns, dry_run=True)

        assert len(results) == 0

    @respx.mock
    def test_get_tag_report(self, client: ReadwiseClient) -> None:
        """Test getting tag report."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test 1", "tags": [{"id": 1, "name": "tag1"}]},
                {"id": 2, "text": "Test 2", "tags": [{"id": 1, "name": "tag1"}]},
                {"id": 3, "text": "Test 3", "tags": [{"id": 2, "name": "tag2"}]},
            ]
        )

        workflow = TagWorkflow(client)
        report = workflow.get_tag_report()

        assert report.total_tags == 2
        assert report.total_usages == 3
        assert ("tag1", 2) in report.tags_by_usage
        assert ("tag2", 1) in report.tags_by_usage

    @respx.mock
    def test_get_highlights_by_tag(self, client: ReadwiseClient) -> None:
        """Test getting highlights by tag."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test 1", "tags": [{"id": 1, "name": "important"}]},
                {"id": 2, "text": "Test 2", "tags": []},
                {"id": 3, "text": "Test 3", "tags": [{"id": 1, "name": "important"}]},
            ]
        )

        workflow = TagWorkflow(client)
        results = workflow.get_highlights_by_tag("important")

        assert len(results) == 2
        assert results[0].id == 1
        assert results[1].id == 3

    @respx.mock
    def test_get_untagged_highlights(self, client: ReadwiseClient) -> None:
        """Test getting untagged highlights."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test 1", "tags": [{"id": 1, "name": "tag1"}]},
                {"id": 2, "text": "Test 2", "tags": []},
                {"id": 3, "text": "Test 3"},
            ]
        )

        workflow = TagWorkflow(client)
        results = workflow.get_untagged_highlights()

        assert len(results) == 2
        assert results[0].id == 2
        assert results[1].id == 3

    @respx.mock
    def test_merge_tags_dry_run(self, client: ReadwiseClient) -> None:
        """Test merging tags in dry run mode."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test 1", "tags": [{"id": 1, "name": "Python"}]},
                {"id": 2, "text": "Test 2", "tags": [{"id": 2, "name": "python"}]},
                {"id": 3, "text": "Test 3", "tags": [{"id": 3, "name": "PYTHON"}]},
            ]
        )

        workflow = TagWorkflow(client)
        affected = workflow.merge_tags(["Python", "python", "PYTHON"], "python", dry_run=True)

        assert len(affected) == 3

    @respx.mock
    def test_rename_tag_dry_run(self, client: ReadwiseClient) -> None:
        """Test renaming tag in dry run mode."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test 1", "tags": [{"id": 1, "name": "old-name"}]},
                {"id": 2, "text": "Test 2", "tags": []},
            ]
        )

        workflow = TagWorkflow(client)
        affected = workflow.rename_tag("old-name", "new-name", dry_run=True)

        assert affected == [1]

    @respx.mock
    def test_delete_tag_dry_run(self, client: ReadwiseClient) -> None:
        """Test deleting tag in dry run mode."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test 1", "tags": [{"id": 1, "name": "to-delete"}]},
                {"id": 2, "text": "Test 2", "tags": [{"id": 1, "name": "to-delete"}]},
            ]
        )

        workflow = TagWorkflow(client)
        affected = workflow.delete_tag("to-delete", dry_run=True)

        assert len(affected) == 2

    @respx.mock
    def test_auto_tag_apply(self, client: ReadwiseClient) -> None:
        """Test auto-tagging with dry_run=False actually creates tags via API."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Python is great", "tags": []},
                {"id": 2, "text": "No match here", "tags": []},
            ]
        )
        tag_route = respx.post(url__startswith=f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(200, json={"id": 99, "name": "programming"})
        )

        workflow = TagWorkflow(client)
        patterns = [TagPattern(pattern=r"python", tag="programming")]
        results = workflow.auto_tag_highlights(patterns, dry_run=False)

        assert 1 in results
        assert "programming" in results[1]
        assert 2 not in results
        assert tag_route.called

    @respx.mock
    def test_merge_tags_apply(self, client: ReadwiseClient) -> None:
        """Test merging tags with dry_run=False actually merges via API."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test 1", "tags": [{"id": 10, "name": "Python"}]},
                {"id": 2, "text": "Test 2", "tags": [{"id": 20, "name": "python"}]},
            ]
        )
        create_route = respx.post(url__startswith=f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(200, json={"id": 99, "name": "py"})
        )
        delete_route = respx.delete(url__startswith=f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(204)
        )

        workflow = TagWorkflow(client)
        affected = workflow.merge_tags(["Python", "python"], "py", dry_run=False)

        assert len(affected) == 2
        assert create_route.called
        assert delete_route.called

    @respx.mock
    def test_rename_tag_apply(self, client: ReadwiseClient) -> None:
        """Test renaming a tag with dry_run=False actually renames via API."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test 1", "tags": [{"id": 10, "name": "old-name"}]},
                {"id": 2, "text": "Test 2", "tags": []},
            ]
        )
        patch_route = respx.patch(url__startswith=f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(200, json={"id": 10, "name": "new-name"})
        )

        workflow = TagWorkflow(client)
        affected = workflow.rename_tag("old-name", "new-name", dry_run=False)

        assert affected == [1]
        assert patch_route.called

    @respx.mock
    def test_delete_tag_apply(self, client: ReadwiseClient) -> None:
        """Test deleting a tag with dry_run=False actually deletes via API."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test 1", "tags": [{"id": 10, "name": "to-delete"}]},
                {"id": 2, "text": "Test 2", "tags": [{"id": 20, "name": "to-delete"}]},
            ]
        )
        delete_route = respx.delete(url__startswith=f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(204)
        )

        workflow = TagWorkflow(client)
        affected = workflow.delete_tag("to-delete", dry_run=False)

        assert len(affected) == 2
        assert delete_route.called

    @respx.mock
    def test_find_similar_tags_with_duplicates(self, client: ReadwiseClient) -> None:
        """Test detecting actual duplicate tag groups from similar tag names."""
        mock_v2_highlights(
            [
                {"id": 1, "text": "Test 1", "tags": [{"id": 1, "name": "machine-learning"}]},
                {"id": 2, "text": "Test 2", "tags": [{"id": 2, "name": "MachineLearning"}]},
                {"id": 3, "text": "Test 3", "tags": [{"id": 3, "name": "machine_learning"}]},
                {"id": 4, "text": "Test 4", "tags": [{"id": 4, "name": "unique-tag"}]},
            ]
        )

        workflow = TagWorkflow(client)
        report = workflow.get_tag_report()

        assert len(report.duplicate_candidates) >= 1
        found_ml_group = False
        for group in report.duplicate_candidates:
            normalized = {g.lower().replace("-", "").replace("_", "") for g in group}
            if "machinelearning" in normalized:
                found_ml_group = True
                assert len(group) == 3
        assert found_ml_group
