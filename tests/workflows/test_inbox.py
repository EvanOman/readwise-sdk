"""Tests for ReadingInbox workflow."""

from datetime import UTC, datetime, timedelta

import httpx
import respx

from readwise_sdk.client import READWISE_API_V3_BASE, ReadwiseClient
from readwise_sdk.v3.models import Document, DocumentCategory
from readwise_sdk.workflows.inbox import (
    ArchiveRule,
    ReadingInbox,
    create_category_rule,
    create_domain_rule,
    create_old_item_rule,
    create_title_pattern_rule,
)
from tests.workflows.conftest import mock_v3_documents


class TestArchiveRules:
    """Tests for archive rule creation."""

    def test_create_old_item_rule(self) -> None:
        """Test creating old item rule."""
        rule = create_old_item_rule(30)
        assert rule.name == "older_than_30_days"

        old_doc = Document(
            id="1",
            url="https://example.com",
            created_at=datetime.now(UTC) - timedelta(days=60),
        )
        new_doc = Document(
            id="2",
            url="https://example.com",
            created_at=datetime.now(UTC) - timedelta(days=10),
        )

        assert rule.condition(old_doc) is True
        assert rule.condition(new_doc) is False

    def test_create_category_rule(self) -> None:
        """Test creating category rule."""
        rule = create_category_rule(DocumentCategory.TWEET)
        assert rule.name == "category_tweet"

        tweet_doc = Document(
            id="1", url="https://twitter.com/test", category=DocumentCategory.TWEET
        )
        article_doc = Document(id="2", url="https://example.com", category=DocumentCategory.ARTICLE)

        assert rule.condition(tweet_doc) is True
        assert rule.condition(article_doc) is False

    def test_create_title_pattern_rule(self) -> None:
        """Test creating title pattern rule."""
        rule = create_title_pattern_rule(r"newsletter", "newsletters")
        assert rule.name == "newsletters"

        newsletter_doc = Document(
            id="1", url="https://example.com", title="Weekly Newsletter: Tech Updates"
        )
        article_doc = Document(id="2", url="https://example.com", title="How to Code Better")

        assert rule.condition(newsletter_doc) is True
        assert rule.condition(article_doc) is False

    def test_create_domain_rule(self) -> None:
        """Test creating domain rule."""
        rule = create_domain_rule("twitter.com")
        assert rule.name == "domain_twitter.com"

        twitter_doc = Document(id="1", url="https://twitter.com/user/status/123")
        other_doc = Document(id="2", url="https://example.com/article")

        assert rule.condition(twitter_doc) is True
        assert rule.condition(other_doc) is False

    def test_rule_none_guards(self) -> None:
        """Test archive rules with documents that have None created_at, title, url."""
        old_rule = create_old_item_rule(30)
        assert (
            old_rule.condition(Document(id="1", url="https://example.com", created_at=None))
            is False
        )

        title_rule = create_title_pattern_rule(r"newsletter", "newsletters")
        assert (
            title_rule.condition(Document(id="2", url="https://example.com", title=None)) is False
        )

        domain_rule = create_domain_rule("twitter.com")
        assert domain_rule.condition(Document(id="3", url="https://placeholder.com")) is False


class TestReadingInbox:
    """Tests for ReadingInbox."""

    @respx.mock
    def test_get_queue_stats(self, client: ReadwiseClient) -> None:
        """Test getting queue statistics."""
        now = datetime.now(UTC)

        def mock_response(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if "location=new" in url:
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "id": "doc1",
                                "url": "https://a.com",
                                "category": "article",
                                "created_at": (now - timedelta(days=10)).isoformat(),
                            },
                            {
                                "id": "doc2",
                                "url": "https://b.com",
                                "category": "article",
                                "created_at": (now - timedelta(days=45)).isoformat(),
                            },
                        ],
                        "nextPageCursor": None,
                    },
                )
            elif "location=later" in url:
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "id": "doc3",
                                "url": "https://c.com",
                                "category": "pdf",
                                "created_at": (now - timedelta(days=5)).isoformat(),
                            }
                        ],
                        "nextPageCursor": None,
                    },
                )
            else:
                return httpx.Response(200, json={"results": [], "nextPageCursor": None})

        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(side_effect=mock_response)

        inbox = ReadingInbox(client)
        stats = inbox.get_queue_stats()

        assert stats.inbox_count == 2
        assert stats.reading_list_count == 1
        assert stats.total_unread == 3
        assert stats.items_older_than_30_days == 1
        assert stats.by_category["article"] == 2
        assert stats.by_category["pdf"] == 1

    @respx.mock
    def test_smart_archive_dry_run(self, client: ReadwiseClient) -> None:
        """Test smart archive in dry run mode."""
        now = datetime.now(UTC)
        mock_v3_documents(
            [
                {
                    "id": "doc1",
                    "url": "https://twitter.com/test",
                    "title": "Tweet",
                    "category": "tweet",
                    "created_at": now.isoformat(),
                },
                {
                    "id": "doc2",
                    "url": "https://example.com",
                    "title": "Article",
                    "category": "article",
                    "created_at": now.isoformat(),
                },
            ]
        )

        inbox = ReadingInbox(client)
        inbox.add_archive_rule(create_category_rule(DocumentCategory.TWEET))

        actions = inbox.smart_archive(dry_run=True)

        assert len(actions) == 1
        assert actions[0].document_id == "doc1"
        assert actions[0].action == "archive"

    @respx.mock
    def test_get_stale_items(self, client: ReadwiseClient) -> None:
        """Test getting stale items."""
        now = datetime.now(UTC)
        mock_v3_documents(
            [
                {
                    "id": "doc1",
                    "url": "https://a.com",
                    "created_at": (now - timedelta(days=60)).isoformat(),
                },
                {
                    "id": "doc2",
                    "url": "https://b.com",
                    "created_at": (now - timedelta(days=10)).isoformat(),
                },
            ]
        )

        inbox = ReadingInbox(client)
        stale = inbox.get_stale_items(days=30)

        assert len(stale) == 1
        assert stale[0].id == "doc1"

    @respx.mock
    def test_search_inbox(self, client: ReadwiseClient) -> None:
        """Test searching inbox."""
        mock_v3_documents(
            [
                {"id": "doc1", "url": "https://a.com", "title": "Python Tutorial"},
                {"id": "doc2", "url": "https://b.com", "title": "JavaScript Guide"},
            ]
        )

        inbox = ReadingInbox(client)
        results = inbox.search_inbox("python")

        assert len(results) == 1
        assert results[0].id == "doc1"

    @respx.mock
    def test_get_inbox_by_priority(self, client: ReadwiseClient) -> None:
        """Test getting inbox sorted by priority."""
        now = datetime.now(UTC)
        mock_v3_documents(
            [
                {
                    "id": "doc1",
                    "url": "https://a.com",
                    "title": "Old PDF",
                    "category": "pdf",
                    "created_at": (now - timedelta(days=30)).isoformat(),
                },
                {
                    "id": "doc2",
                    "url": "https://b.com",
                    "title": "New Article",
                    "category": "article",
                    "created_at": now.isoformat(),
                },
            ]
        )

        inbox = ReadingInbox(client)
        prioritized = inbox.get_inbox_by_priority()

        assert prioritized[0].id == "doc2"
        assert prioritized[1].id == "doc1"

    @respx.mock
    def test_get_inbox_categories(self, client: ReadwiseClient) -> None:
        """Test getting inbox grouped by category."""
        mock_v3_documents(
            [
                {"id": "doc1", "url": "https://a.com", "category": "article"},
                {"id": "doc2", "url": "https://b.com", "category": "article"},
                {"id": "doc3", "url": "https://c.com", "category": "pdf"},
            ]
        )

        inbox = ReadingInbox(client)
        categories = inbox.get_inbox_categories()

        assert len(categories[DocumentCategory.ARTICLE]) == 2
        assert len(categories[DocumentCategory.PDF]) == 1

    def test_add_remove_archive_rules(self, client: ReadwiseClient) -> None:
        """Test adding and removing archive rules."""
        inbox = ReadingInbox(client)

        rule = create_old_item_rule(30)
        inbox.add_archive_rule(rule)
        assert len(inbox.get_archive_rules()) == 1

        assert inbox.remove_archive_rule("older_than_30_days") is True
        assert len(inbox.get_archive_rules()) == 0

        assert inbox.remove_archive_rule("non_existent") is False

    @respx.mock
    def test_move_to_reading_list(self, client: ReadwiseClient) -> None:
        """Test moving documents to reading list."""
        respx.patch(url__startswith=f"{READWISE_API_V3_BASE}/update/").mock(
            return_value=httpx.Response(200, json={"id": "doc1", "url": "https://example.com"})
        )

        inbox = ReadingInbox(client)
        results = inbox.move_to_reading_list(["doc1", "doc2"])

        assert results["doc1"] is True
        assert results["doc2"] is True

    @respx.mock
    def test_smart_archive_apply(self, client: ReadwiseClient) -> None:
        """Test smart archive with dry_run=False actually archives via API."""
        now = datetime.now(UTC)
        mock_v3_documents(
            [
                {
                    "id": "doc1",
                    "url": "https://twitter.com/test",
                    "title": "Tweet",
                    "category": "tweet",
                    "created_at": now.isoformat(),
                },
                {
                    "id": "doc2",
                    "url": "https://example.com",
                    "title": "Article",
                    "category": "article",
                    "created_at": now.isoformat(),
                },
            ]
        )
        archive_route = respx.patch(url__startswith=f"{READWISE_API_V3_BASE}/update/").mock(
            return_value=httpx.Response(200, json={"id": "doc1", "url": "https://twitter.com/test"})
        )

        inbox = ReadingInbox(client)
        inbox.add_archive_rule(create_category_rule(DocumentCategory.TWEET))

        actions = inbox.smart_archive(dry_run=False)

        assert len(actions) == 1
        assert actions[0].document_id == "doc1"
        assert actions[0].action == "archive"
        assert archive_route.called

    @respx.mock
    def test_smart_archive_disabled_rule(self, client: ReadwiseClient) -> None:
        """Test that disabled rules are skipped in smart archive."""
        now = datetime.now(UTC)
        mock_v3_documents(
            [
                {
                    "id": "doc1",
                    "url": "https://twitter.com/test",
                    "title": "Tweet",
                    "category": "tweet",
                    "created_at": now.isoformat(),
                },
            ]
        )

        inbox = ReadingInbox(client)
        disabled_rule = ArchiveRule(
            name="disabled_tweet_rule",
            condition=lambda doc: doc.category == DocumentCategory.TWEET,
            enabled=False,
        )
        inbox.add_archive_rule(disabled_rule)

        actions = inbox.smart_archive(dry_run=True)

        assert len(actions) == 0

    @respx.mock
    def test_batch_archive_stale(self, client: ReadwiseClient) -> None:
        """Test batch_archive_stale method."""
        now = datetime.now(UTC)

        def mock_response(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if "location=new" in url:
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "id": "doc1",
                                "url": "https://a.com",
                                "title": "Old Article",
                                "created_at": (now - timedelta(days=100)).isoformat(),
                            },
                        ],
                        "nextPageCursor": None,
                    },
                )
            elif "location=later" in url:
                return httpx.Response(
                    200,
                    json={
                        "results": [
                            {
                                "id": "doc2",
                                "url": "https://b.com",
                                "title": "Old Later Item",
                                "created_at": (now - timedelta(days=120)).isoformat(),
                            },
                        ],
                        "nextPageCursor": None,
                    },
                )
            else:
                return httpx.Response(200, json={"results": [], "nextPageCursor": None})

        respx.get(f"{READWISE_API_V3_BASE}/list/").mock(side_effect=mock_response)
        archive_route = respx.patch(url__startswith=f"{READWISE_API_V3_BASE}/update/").mock(
            return_value=httpx.Response(200, json={"id": "doc1", "url": "https://a.com"})
        )

        inbox = ReadingInbox(client)
        actions = inbox.batch_archive_stale(days=90, dry_run=False)

        assert len(actions) == 2
        assert actions[0].document_id == "doc1"
        assert actions[1].document_id == "doc2"
        assert actions[0].reason is not None and "Older than 90 days" in actions[0].reason
        assert archive_route.called

    @respx.mock
    def test_move_to_reading_list_error(self, client: ReadwiseClient) -> None:
        """Test move_to_reading_list when API returns an error."""
        respx.patch(url__startswith=f"{READWISE_API_V3_BASE}/update/").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        inbox = ReadingInbox(client)
        results = inbox.move_to_reading_list(["doc1"])

        assert results["doc1"] is False
