"""Live tests against the real Readwise API.

These tests require a valid READWISE_API_KEY environment variable.
Run with: pytest -m live
"""

import os
from datetime import UTC, datetime, timedelta

import pytest

from readwise_sdk import (
    BookManager,
    DigestBuilder,
    DigestFormat,
    DocumentManager,
    HighlightManager,
    ReadwiseClient,
    SyncManager,
)
from readwise_sdk.workflows.inbox import ReadingInbox
from readwise_sdk.workflows.tags import TagWorkflow

# Skip all tests in this module if no API key is set
pytestmark = pytest.mark.live


@pytest.fixture
def client() -> ReadwiseClient:
    """Get a live Readwise client."""
    api_key = os.environ.get("READWISE_API_KEY")
    if not api_key:
        pytest.skip("READWISE_API_KEY environment variable not set")
    return ReadwiseClient(api_key=api_key)


class TestLiveAuthentication:
    """Test authentication against live API."""

    def test_validate_token(self, client: ReadwiseClient) -> None:
        """Test that the API token is valid."""
        is_valid = client.validate_token()
        assert is_valid is True


class TestLiveV2Highlights:
    """Test V2 highlights API."""

    def test_list_highlights(self, client: ReadwiseClient) -> None:
        """Test listing highlights."""
        highlights = list(client.v2.list_highlights())
        print(f"\nFound {len(highlights)} highlights")
        assert isinstance(highlights, list)

        if highlights:
            h = highlights[0]
            print(f"First highlight: {h.text[:100]}...")
            assert h.id is not None
            assert h.text is not None

    def test_list_highlights_with_limit(self, client: ReadwiseClient) -> None:
        """Test listing highlights with page size."""
        highlights = []
        for i, h in enumerate(client.v2.list_highlights(page_size=5)):
            highlights.append(h)
            if i >= 9:  # Get 10 highlights max
                break

        print(f"\nFetched {len(highlights)} highlights (limited)")
        assert len(highlights) <= 10

    def test_list_highlights_updated_after(self, client: ReadwiseClient) -> None:
        """Test filtering highlights by update time."""
        since = datetime.now(UTC) - timedelta(days=30)
        highlights = list(client.v2.list_highlights(updated_after=since))
        print(f"\nFound {len(highlights)} highlights updated in last 30 days")
        assert isinstance(highlights, list)


class TestLiveV2Books:
    """Test V2 books API."""

    def test_list_books(self, client: ReadwiseClient) -> None:
        """Test listing books."""
        books = list(client.v2.list_books())
        print(f"\nFound {len(books)} books")
        assert isinstance(books, list)

        if books:
            b = books[0]
            print(f"First book: {b.title} by {b.author} ({b.num_highlights} highlights)")
            assert b.id is not None
            assert b.title is not None

    def test_get_book(self, client: ReadwiseClient) -> None:
        """Test getting a single book."""
        books = list(client.v2.list_books())
        if not books:
            pytest.skip("No books found")

        book = client.v2.get_book(books[0].id)
        print(f"\nBook: {book.title}")
        assert book.id == books[0].id


class TestLiveV3Documents:
    """Test V3 Reader documents API."""

    def test_list_documents(self, client: ReadwiseClient) -> None:
        """Test listing documents."""
        docs = list(client.v3.list_documents())
        print(f"\nFound {len(docs)} documents")
        assert isinstance(docs, list)

        if docs:
            d = docs[0]
            print(f"First doc: {d.title} ({d.category})")
            assert d.id is not None
            assert d.url is not None

    def test_get_inbox(self, client: ReadwiseClient) -> None:
        """Test getting inbox documents."""
        inbox = list(client.v3.get_inbox())
        print(f"\nInbox: {len(inbox)} documents")
        assert isinstance(inbox, list)

    def test_get_reading_list(self, client: ReadwiseClient) -> None:
        """Test getting reading list documents."""
        reading_list = list(client.v3.get_reading_list())
        print(f"\nReading list: {len(reading_list)} documents")
        assert isinstance(reading_list, list)

    def test_get_archive(self, client: ReadwiseClient) -> None:
        """Test getting archived documents."""
        archive = list(client.v3.get_archive())
        print(f"\nArchive: {len(archive)} documents")
        assert isinstance(archive, list)

    def test_list_tags(self, client: ReadwiseClient) -> None:
        """Test listing document tags."""
        tags = list(client.v3.list_tags())
        print(f"\nFound {len(tags)} tags")
        if tags:
            print(f"Tags: {[t.name for t in tags[:10]]}")
        assert isinstance(tags, list)


class TestLiveManagers:
    """Test high-level managers."""

    def test_highlight_manager(self, client: ReadwiseClient) -> None:
        """Test HighlightManager."""
        manager = HighlightManager(client)

        # Get count
        count = manager.get_highlight_count()
        print(f"\nTotal highlights: {count}")
        assert count >= 0

        # Get highlights with notes
        with_notes = manager.get_highlights_with_notes()
        print(f"Highlights with notes: {len(with_notes)}")

        # Search
        if count > 0:
            results = manager.search_highlights("the")
            print(f"Highlights containing 'the': {len(results)}")

    def test_book_manager(self, client: ReadwiseClient) -> None:
        """Test BookManager."""
        manager = BookManager(client)

        # Get all books
        books = manager.get_all_books()
        print(f"\nTotal books: {len(books)}")

        # Get reading stats
        stats = manager.get_reading_stats()
        print("Reading stats:")
        print(f"  Total books: {stats.total_books}")
        print(f"  Total highlights: {stats.total_highlights}")
        print(f"  By category: {stats.books_by_category}")

        # Get recent books
        recent = manager.get_recent_books(days=30, limit=5)
        print(f"Recent books (30 days): {len(recent)}")

    def test_document_manager(self, client: ReadwiseClient) -> None:
        """Test DocumentManager."""
        manager = DocumentManager(client)

        # Get inbox
        inbox = manager.get_inbox()
        print(f"\nInbox: {len(inbox)} documents")

        # Get reading list
        reading_list = manager.get_reading_list()
        print(f"Reading list: {len(reading_list)} documents")

        # Get unread count
        unread = manager.get_unread_count()
        print(f"Unread: {unread}")

        # Get inbox stats
        stats = manager.get_inbox_stats()
        print("Inbox stats:")
        print(f"  Inbox: {stats.inbox_count}")
        print(f"  Reading list: {stats.reading_list_count}")
        print(f"  Archive: {stats.archive_count}")
        print(f"  By category: {stats.by_category}")

    def test_sync_manager(self, client: ReadwiseClient) -> None:
        """Test SyncManager with incremental sync."""
        manager = SyncManager(client)

        # Do incremental sync (highlights only for speed)
        result = manager.incremental_sync(include_books=False, include_documents=False)
        print("\nSync result:")
        print(f"  Highlights: {len(result.highlights)}")
        print(f"  Total syncs: {manager.state.total_syncs}")


class TestLiveWorkflows:
    """Test workflow utilities."""

    def test_digest_builder(self, client: ReadwiseClient) -> None:
        """Test DigestBuilder."""
        builder = DigestBuilder(client)

        # Create daily digest
        daily = builder.create_daily_digest(output_format=DigestFormat.MARKDOWN)
        print(f"\nDaily digest length: {len(daily)} chars")
        assert "Daily Digest" in daily

        # Create JSON digest
        json_digest = builder.create_daily_digest(output_format=DigestFormat.JSON)
        assert '"title"' in json_digest

    def test_reading_inbox(self, client: ReadwiseClient) -> None:
        """Test ReadingInbox workflow."""
        inbox = ReadingInbox(client)

        # Get queue stats
        stats = inbox.get_queue_stats()
        print("\nQueue stats:")
        print(f"  Total unread: {stats.total_unread}")
        print(f"  Oldest item: {stats.oldest_item_age_days} days")
        print(f"  Items > 30 days: {stats.items_older_than_30_days}")

        # Get stale items
        stale = inbox.get_stale_items(days=60)
        print(f"Stale items (>60 days): {len(stale)}")

        # Get by priority
        prioritized = inbox.get_inbox_by_priority()
        print(f"Prioritized inbox: {len(prioritized)} items")

    def test_tag_workflow(self, client: ReadwiseClient) -> None:
        """Test TagWorkflow."""
        workflow = TagWorkflow(client)

        # Get tag report
        report = workflow.get_tag_report()
        print("\nTag report:")
        print(f"  Total tags: {report.total_tags}")
        print(f"  Total usages: {report.total_usages}")
        print(f"  Top 5 tags: {report.tags_by_usage[:5]}")
        print(f"  Duplicate candidates: {report.duplicate_candidates[:3]}")

        # Get untagged highlights
        untagged = workflow.get_untagged_highlights()
        print(f"Untagged highlights: {len(untagged)}")


class TestLiveExport:
    """Test export functionality."""

    def test_export_highlights(self, client: ReadwiseClient) -> None:
        """Test exporting highlights."""
        # Export with pagination
        exports = []
        for book in client.v2.export_highlights():
            exports.append(book)
            if len(exports) >= 5:
                break

        print(f"\nExported {len(exports)} books")
        if exports:
            b = exports[0]
            print(f"First: {b.title} with {len(b.highlights)} highlights")

    def test_daily_review(self, client: ReadwiseClient) -> None:
        """Test daily review."""
        review = client.v2.get_daily_review()
        print(f"\nDaily review: {len(review.highlights)} highlights")

        if review.highlights:
            h = review.highlights[0]
            print(f"First highlight: {h.text[:80]}...")


def test_full_integration(client: ReadwiseClient) -> None:
    """Full integration test across all modules (with limited data for speed)."""
    print("\n" + "=" * 60)
    print("FULL INTEGRATION TEST")
    print("=" * 60)

    # 1. Validate token
    assert client.validate_token()
    print("✓ Token valid")

    # 2. Get highlights (limited to 10)
    highlights = []
    for i, h in enumerate(client.v2.list_highlights()):
        highlights.append(h)
        if i >= 9:
            break
    print(f"✓ Fetched {len(highlights)} highlights (sample)")

    # 3. Get books (limited to 10)
    books = []
    for i, b in enumerate(client.v2.list_books()):
        books.append(b)
        if i >= 9:
            break
    print(f"✓ Fetched {len(books)} books (sample)")

    # 4. Get documents (limited to 10)
    docs = []
    for i, d in enumerate(client.v3.list_documents()):
        docs.append(d)
        if i >= 9:
            break
    print(f"✓ Fetched {len(docs)} documents (sample)")

    # 5. Get inbox (limited)
    inbox = []
    for i, d in enumerate(client.v3.get_inbox()):
        inbox.append(d)
        if i >= 4:
            break
    print(f"✓ Inbox sample: {len(inbox)} items")

    # 6. Create digest (uses limited data from last 24h)
    builder = DigestBuilder(client)
    digest = builder.create_daily_digest()
    print(f"✓ Created digest ({len(digest)} chars)")

    # 7. List tags
    tags = list(client.v3.list_tags())
    print(f"✓ Found {len(tags)} document tags")

    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
