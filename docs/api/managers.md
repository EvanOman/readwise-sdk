# Managers

Managers provide high-level abstractions over the core API.

## HighlightManager

```python
from readwise_sdk.managers import HighlightManager

manager = HighlightManager(client)
```

### Methods

#### get_all_highlights

```python
highlights = manager.get_all_highlights()
```

#### get_highlights_since

```python
# By days
highlights = manager.get_highlights_since(days=7)

# By hours
highlights = manager.get_highlights_since(hours=24)

# By specific datetime
from datetime import datetime
highlights = manager.get_highlights_since(since=datetime(2024, 1, 1))
```

#### get_highlights_by_book

```python
highlights = manager.get_by_book(book_id=123)
```

#### get_highlights_with_notes

```python
highlights = manager.get_highlights_with_notes()
```

#### search

```python
results = manager.search("machine learning")
```

#### bulk_tag

```python
manager.bulk_tag(highlight_ids=[1, 2, 3], tag_name="review")
```

#### create_highlight

```python
highlight_id = manager.create_highlight(
    text="Important quote",
    title="Book Title",
    author="Author",
)
```

#### get_highlight_count

```python
count = manager.get_highlight_count()
```

## BookManager

```python
from readwise_sdk.managers import BookManager

manager = BookManager(client)
```

### Methods

#### list

```python
books = manager.list()
```

#### get_by_category

```python
articles = manager.get_by_category("articles")
```

#### get_with_highlights

```python
book = manager.get_with_highlights(book_id=123)
print(len(book.highlights))
```

#### search

```python
results = manager.search("Python")
```

#### get_reading_stats

```python
stats = manager.get_reading_stats()
print(stats['total_books'])
print(stats['total_highlights'])
```

## DocumentManager

```python
from readwise_sdk.managers import DocumentManager

manager = DocumentManager(client)
```

### Methods

#### get_inbox

```python
docs = manager.get_inbox()
```

#### get_reading_list

```python
docs = manager.get_reading_list()
```

#### get_archive

```python
docs = manager.get_archive()
```

#### get_documents_since

```python
docs = manager.get_documents_since(days=7)
```

#### bulk_archive

```python
manager.bulk_archive(document_ids=["doc1", "doc2", "doc3"])
```

#### search

```python
results = manager.search("machine learning")
```

#### get_inbox_stats

```python
stats = manager.get_inbox_stats()
print(f"Total unread: {stats.total_unread}")
print(f"Oldest item: {stats.oldest_item_age_days} days")
```

#### get_documents_by_category

```python
from readwise_sdk.v3.models import DocumentCategory
articles = manager.get_documents_by_category(DocumentCategory.ARTICLE)
```

## SyncManager

```python
from readwise_sdk.managers import SyncManager

manager = SyncManager(client, state_file="sync.json")
```

### Methods

#### full_sync

```python
result = manager.full_sync()
print(f"Highlights: {len(result.highlights)}")
print(f"Books: {len(result.books)}")
print(f"Documents: {len(result.documents)}")
```

#### incremental_sync

```python
result = manager.incremental_sync()
print(f"New highlights: {len(result.highlights)}")
```

#### reset_state

```python
manager.reset_state()
```

### Properties

#### state

```python
print(f"Last sync: {manager.state.last_sync}")
print(f"Total syncs: {manager.state.total_syncs}")
```
