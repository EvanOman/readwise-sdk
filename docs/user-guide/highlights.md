# Working with Highlights

Highlights are the core data type in Readwise. This guide covers how to read, create, and manage highlights.

## Listing Highlights

### Basic Listing

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient()

# Iterate through all highlights
for highlight in client.v2.list_highlights():
    print(f"[{highlight.id}] {highlight.text[:50]}...")
```

### With Filters

```python
from datetime import datetime, timedelta

# Filter by book
highlights = client.v2.list_highlights(book_id=12345)

# Filter by date
since = datetime.now() - timedelta(days=30)
highlights = client.v2.list_highlights(updated_after=since)
```

### Get a Single Highlight

```python
highlight = client.v2.get_highlight(highlight_id=123456)
print(f"Text: {highlight.text}")
print(f"Note: {highlight.note}")
print(f"Tags: {[t.name for t in highlight.tags]}")
```

## Creating Highlights

### Single Highlight

```python
from readwise_sdk.v2.models import HighlightCreate

highlight = HighlightCreate(
    text="The important quote to save",
    title="Book Title",
    author="Author Name",
    source_type="book",
    note="My thoughts on this quote",
)

ids = client.v2.create_highlights([highlight])
print(f"Created highlight: {ids[0]}")
```

### Multiple Highlights

```python
highlights = [
    HighlightCreate(text="First quote", title="Book 1"),
    HighlightCreate(text="Second quote", title="Book 2"),
    HighlightCreate(text="Third quote", title="Book 3"),
]

ids = client.v2.create_highlights(highlights)
print(f"Created {len(ids)} highlights")
```

## Using HighlightManager

The `HighlightManager` provides convenient methods for common operations:

```python
from readwise_sdk.managers import HighlightManager

manager = HighlightManager(client)

# Get recent highlights
recent = manager.get_highlights_since(days=7)

# Get highlights with notes
with_notes = manager.get_highlights_with_notes()

# Search highlights
results = manager.search("python programming")

# Get highlights by book
book_highlights = manager.get_by_book(book_id=123)

# Bulk tag highlights
manager.bulk_tag([1, 2, 3], "to-review")
```

## Exporting Highlights

Export all highlights with full book metadata:

```python
for book in client.v2.export_highlights():
    print(f"\n## {book.title}")
    print(f"Author: {book.author}")
    print(f"Highlights: {len(book.highlights)}")

    for h in book.highlights:
        print(f"\n> {h.text}")
        if h.note:
            print(f"Note: {h.note}")
```

## Daily Review

Get your daily review highlights:

```python
review = client.v2.get_daily_review()

print(f"Review for {review.review_id}")
for highlight in review.highlights:
    print(f"\n> {highlight.text}")
    print(f"From: {highlight.title}")
```

## Managing Tags

### Add a Tag

```python
client.v2.create_highlight_tag(highlight_id=123, name="important")
```

### Remove a Tag

```python
client.v2.delete_highlight_tag(highlight_id=123, tag_id=456)
```

### List Tags

```python
tags = client.v2.list_highlight_tags(highlight_id=123)
for tag in tags:
    print(f"- {tag.name}")
```

## Next Steps

- [Working with Books](books.md)
- [Tag Management](tags.md)
- [Workflows](workflows.md)
