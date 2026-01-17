# Reader Documents

The Reader API (v3) manages documents in Readwise Reader - your read-it-later inbox.

## Document Locations

Documents can be in one of three locations:

- **new** - Inbox (unread)
- **later** - Reading list (saved for later)
- **archive** - Archived (read/processed)

## Listing Documents

### Get Inbox

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient()

# Get inbox documents
for doc in client.v3.get_inbox():
    print(f"[{doc.category}] {doc.title}")
```

### Get Reading List

```python
for doc in client.v3.get_reading_list():
    print(f"{doc.title} - {doc.reading_progress*100:.0f}% read")
```

### Get Archive

```python
for doc in client.v3.get_archive():
    print(f"{doc.title}")
```

### Filter by Category

```python
from readwise_sdk.v3.models import DocumentCategory

# Get only articles
articles = client.v3.list_documents(category=DocumentCategory.ARTICLE)

# Get only PDFs
pdfs = client.v3.list_documents(category=DocumentCategory.PDF)
```

Available categories:

- `ARTICLE` - Web articles
- `EMAIL` - Email newsletters
- `RSS` - RSS feed items
- `HIGHLIGHT` - Highlighted content
- `NOTE` - Notes
- `PDF` - PDF documents
- `EPUB` - EPUB books
- `TWEET` - Twitter content
- `VIDEO` - Videos

## Saving URLs

### Basic Save

```python
result = client.v3.save_url("https://example.com/article")
print(f"Saved as: {result.id}")
```

### Save with Options

```python
result = client.v3.save_url(
    "https://example.com/article",
    tags=["to-read", "tech"],
    location="later",  # Save directly to reading list
)
```

## Moving Documents

```python
# Move to reading list
client.v3.move_to_later(document_id)

# Archive
client.v3.archive(document_id)

# Move back to inbox
client.v3.move_to_inbox(document_id)
```

## Using DocumentManager

The `DocumentManager` provides higher-level operations:

```python
from readwise_sdk.managers import DocumentManager

manager = DocumentManager(client)

# Get inbox with stats
inbox = manager.get_inbox()
print(f"Inbox: {len(inbox)} documents")

# Get recent documents
recent = manager.get_documents_since(days=7)

# Bulk archive
manager.bulk_archive([doc1_id, doc2_id, doc3_id])

# Search documents
results = manager.search("machine learning")

# Get inbox statistics
stats = manager.get_inbox_stats()
print(f"Total unread: {stats.total_unread}")
print(f"Oldest item: {stats.oldest_item_age_days} days")
```

## Reading Inbox Workflow

The `ReadingInbox` workflow helps manage your inbox:

```python
from readwise_sdk.workflows import ReadingInbox

inbox = ReadingInbox(client)

# Get queue statistics
stats = inbox.get_queue_stats()
print(f"Inbox: {stats.inbox_count}")
print(f"Reading List: {stats.reading_list_count}")

# Get stale items (older than 30 days)
stale = inbox.get_stale_items(days=30)

# Smart archive with rules
from readwise_sdk.workflows.inbox import ArchiveRules

rules = ArchiveRules()
rules.add_old_item_rule(days=90)  # Archive items > 90 days
rules.add_category_rule("tweet")  # Archive all tweets

result = inbox.smart_archive(rules, dry_run=True)
print(f"Would archive {len(result)} documents")
```

## Document Importer (Contrib)

The `DocumentImporter` provides metadata extraction:

```python
from readwise_sdk.contrib import DocumentImporter

importer = DocumentImporter(client)

# Import with metadata extraction
doc = importer.import_document(doc_id, with_content=True)
print(f"Title: {doc.title}")
print(f"Domain: {doc.domain}")
print(f"Word count: {doc.word_count}")
print(f"Reading time: {doc.reading_time_minutes} mins")
print(f"Clean text: {doc.clean_text[:200]}...")
```

## Next Steps

- [Tag Management](tags.md)
- [Workflows](workflows.md)
- [CLI Reference](../cli.md)
