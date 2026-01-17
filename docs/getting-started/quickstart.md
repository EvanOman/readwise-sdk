# Quick Start

This guide will help you get started with readwise-plus in just a few minutes.

## Prerequisites

1. [Install readwise-plus](installation.md)
2. [Set up authentication](authentication.md)

## Basic Usage

### List Your Highlights

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient()

# Get your 10 most recent highlights
for i, highlight in enumerate(client.v2.list_highlights()):
    if i >= 10:
        break
    print(f"- {highlight.text[:80]}...")
```

### List Your Books

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient()

# Get all books with highlights
for book in client.v2.list_books():
    print(f"{book.title} by {book.author}: {book.num_highlights} highlights")
```

### Access Reader Inbox

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient()

# Get documents in your Reader inbox
for doc in client.v3.get_inbox():
    print(f"[{doc.category}] {doc.title}")
```

### Save a URL to Reader

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient()

result = client.v3.save_url("https://example.com/article")
print(f"Saved! Document ID: {result.id}")
```

## Using Managers

Managers provide higher-level operations:

```python
from readwise_sdk import ReadwiseClient
from readwise_sdk.managers import HighlightManager

client = ReadwiseClient()
highlights = HighlightManager(client)

# Get highlights from the last 7 days
recent = highlights.get_highlights_since(days=7)
print(f"Found {len(recent)} highlights from the last week")

# Search highlights
results = highlights.search("machine learning")
for h in results:
    print(f"- {h.text[:60]}...")
```

## Using Workflows

Workflows automate common tasks:

```python
from readwise_sdk import ReadwiseClient
from readwise_sdk.workflows import DigestBuilder

client = ReadwiseClient()
builder = DigestBuilder(client)

# Create a daily digest
digest = builder.create_daily_digest()
print(digest)  # Markdown formatted digest
```

## Using the CLI

The CLI provides quick access from the command line:

```bash
# List recent highlights
readwise highlights list --limit 10

# View Reader inbox
readwise reader inbox

# Generate a daily digest
readwise digest daily

# Get tag report
readwise tags report
```

## Next Steps

- [Working with Highlights](../user-guide/highlights.md)
- [Working with Books](../user-guide/books.md)
- [Reader Documents](../user-guide/documents.md)
- [CLI Reference](../cli.md)
