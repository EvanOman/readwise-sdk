# Working with Books

Books in Readwise represent sources of highlights - including actual books, articles, tweets, and podcasts.

## Listing Books

### Basic Listing

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient()

for book in client.v2.list_books():
    print(f"{book.title} - {book.num_highlights} highlights")
```

### Filter by Category

```python
from readwise_sdk.v2.models import BookCategory

# Get only articles
articles = client.v2.list_books(category=BookCategory.ARTICLES)

# Get only books
books = client.v2.list_books(category=BookCategory.BOOKS)

# Get tweets
tweets = client.v2.list_books(category=BookCategory.TWEETS)
```

Available categories:

- `BookCategory.BOOKS` - Traditional books
- `BookCategory.ARTICLES` - Web articles
- `BookCategory.TWEETS` - Twitter threads
- `BookCategory.PODCASTS` - Podcast episodes
- `BookCategory.SUPPLEMENTALS` - Supplemental content

### Get a Single Book

```python
book = client.v2.get_book(book_id=12345)

print(f"Title: {book.title}")
print(f"Author: {book.author}")
print(f"Category: {book.category}")
print(f"Highlights: {book.num_highlights}")
print(f"Source: {book.source}")
```

## Using BookManager

The `BookManager` provides convenient methods:

```python
from readwise_sdk.managers import BookManager

manager = BookManager(client)

# Get all books
all_books = manager.list()

# Get books by category
articles = manager.get_by_category("articles")

# Get book with highlights
book = manager.get_with_highlights(book_id=123)
print(f"Found {len(book.highlights)} highlights")

# Search books
results = manager.search("Python")
```

## Book Statistics

Get reading statistics:

```python
from readwise_sdk.managers import BookManager

manager = BookManager(client)
stats = manager.get_reading_stats()

print(f"Total books: {stats['total_books']}")
print(f"Total highlights: {stats['total_highlights']}")
print(f"By category:")
for cat, count in stats['by_category'].items():
    print(f"  {cat}: {count}")
```

## Book Tags

Books can also have tags:

```python
# List book tags
tags = client.v2.list_book_tags(book_id=123)
for tag in tags:
    print(f"- {tag.name}")

# Add a tag
client.v2.create_book_tag(book_id=123, name="favorites")
```

## Export with Highlights

Export books with their highlights:

```python
for book in client.v2.export_highlights():
    print(f"\n# {book.title}")
    print(f"*{book.author}*\n")

    for h in book.highlights:
        print(f"> {h.text}")
        if h.note:
            print(f"\n**Note:** {h.note}")
        print()
```

## Next Steps

- [Reader Documents](documents.md)
- [Tag Management](tags.md)
- [Creating Digests](workflows.md)
