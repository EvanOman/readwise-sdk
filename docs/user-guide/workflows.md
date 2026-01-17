# Workflows

Workflows automate common tasks like creating digests, managing your inbox, and syncing data.

## DigestBuilder

Create formatted digests of your highlights:

```python
from readwise_sdk import ReadwiseClient
from readwise_sdk.workflows import DigestBuilder

client = ReadwiseClient()
builder = DigestBuilder(client)
```

### Daily Digest

```python
# Markdown format (default)
digest = builder.create_daily_digest()
print(digest)

# JSON format
from readwise_sdk.workflows.digest import DigestFormat
digest = builder.create_daily_digest(output_format=DigestFormat.JSON)
```

### Weekly Digest

```python
digest = builder.create_weekly_digest()
```

### Book Digest

```python
digest = builder.create_book_digest(book_id=12345)
```

### Custom Digest

```python
from datetime import datetime, timedelta

digest = builder.create_custom_digest(
    since=datetime.now() - timedelta(days=14),
    output_format=DigestFormat.MARKDOWN,
)
```

### Output Formats

- `DigestFormat.MARKDOWN` - Formatted markdown
- `DigestFormat.JSON` - Structured JSON
- `DigestFormat.CSV` - CSV format
- `DigestFormat.TEXT` - Plain text

## ReadingInbox

Manage your Reader inbox efficiently:

```python
from readwise_sdk.workflows import ReadingInbox

inbox = ReadingInbox(client)
```

### Queue Statistics

```python
stats = inbox.get_queue_stats()

print(f"Inbox: {stats.inbox_count}")
print(f"Reading List: {stats.reading_list_count}")
print(f"Total Unread: {stats.total_unread}")
print(f"Oldest Item: {stats.oldest_item_age_days} days")
print(f"Average Age: {stats.average_age_days:.1f} days")
print(f"Items > 30 days: {stats.items_older_than_30_days}")
```

### Find Stale Items

```python
# Get items older than 60 days
stale = inbox.get_stale_items(days=60)
for doc in stale:
    print(f"[{doc.created_at}] {doc.title}")
```

### Smart Archive

Archive items based on rules:

```python
from readwise_sdk.workflows.inbox import ArchiveRules

rules = ArchiveRules()
rules.add_old_item_rule(days=90)        # Items older than 90 days
rules.add_category_rule("tweet")         # All tweets
rules.add_domain_rule("twitter.com")     # Items from Twitter
rules.add_title_pattern_rule(r"^\[AD\]") # Items starting with [AD]

# Preview (dry run)
to_archive = inbox.smart_archive(rules, dry_run=True)
print(f"Would archive {len(to_archive)} items")

# Apply
archived = inbox.smart_archive(rules, dry_run=False)
```

### Search Inbox

```python
results = inbox.search("machine learning")
for doc in results:
    print(f"- {doc.title}")
```

### Prioritized Inbox

Get inbox sorted by priority:

```python
prioritized = inbox.get_prioritized(limit=20)
```

## BackgroundPoller

Poll for new content in the background:

```python
from readwise_sdk.workflows import BackgroundPoller, PollerConfig

config = PollerConfig(
    poll_highlights=True,
    poll_documents=True,
    state_file="poller_state.json",
)

poller = BackgroundPoller(client, config=config)

# Register callbacks
def on_new_highlight(highlight):
    print(f"New highlight: {highlight.text[:50]}...")

def on_new_document(document):
    print(f"New document: {document.title}")

poller.on_highlight(on_new_highlight)
poller.on_document(on_new_document)

# Poll once
result = poller.poll_once()
print(f"Found {result.new_highlights} new highlights")
print(f"Found {result.new_documents} new documents")
```

## TagWorkflow

See [Tag Management](tags.md) for detailed tag workflow documentation.

## SyncManager

Synchronize all data with state tracking:

```python
from readwise_sdk.managers import SyncManager

manager = SyncManager(client, state_file="sync_state.json")

# Full sync
result = manager.full_sync()
print(f"Synced {len(result.highlights)} highlights")
print(f"Synced {len(result.books)} books")
print(f"Synced {len(result.documents)} documents")

# Incremental sync (only new/updated items)
result = manager.incremental_sync()
```

## Contrib Interfaces

For integration patterns, see:

- [HighlightPusher](../api/contrib.md#highlightpusher) - Push highlights to Readwise
- [DocumentImporter](../api/contrib.md#documentimporter) - Import documents with metadata
- [BatchSync](../api/contrib.md#batchsync) - Batch synchronization with callbacks

## CLI Integration

Most workflows are available via CLI:

```bash
# Digests
readwise digest daily
readwise digest weekly
readwise digest book 12345

# Sync
readwise sync full
readwise sync incremental --state-file sync.json

# Reader stats
readwise reader stats
```

## Next Steps

- [CLI Reference](../cli.md)
- [API Reference](../api/client.md)
