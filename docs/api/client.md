# Client

The `ReadwiseClient` is the main entry point for the SDK. Both synchronous and asynchronous clients are available.

## ReadwiseClient

::: readwise_sdk.client.ReadwiseClient
    options:
      show_source: false
      members:
        - __init__
        - validate_token
        - v2
        - v3

## Usage

```python
from readwise_sdk import ReadwiseClient

# Using environment variable
client = ReadwiseClient()

# Explicit API key
client = ReadwiseClient(api_key="your_key")

# As context manager
with ReadwiseClient() as client:
    highlights = list(client.v2.list_highlights())
```

## Properties

### v2

Access the V2 API client for Readwise (highlights, books, tags):

```python
client.v2.list_highlights()
client.v2.list_books()
client.v2.get_daily_review()
```

See [V2 API Reference](v2.md) for details.

### v3

Access the V3 API client for Reader (documents):

```python
client.v3.list_documents()
client.v3.save_url("https://example.com")
client.v3.archive(doc_id)
```

See [V3 API Reference](v3.md) for details.

## Exceptions

The SDK raises typed exceptions:

```python
from readwise_sdk.exceptions import (
    ReadwiseError,           # Base exception
    AuthenticationError,     # Invalid API key
    RateLimitError,          # Rate limit exceeded
    NotFoundError,           # Resource not found
    ValidationError,         # Invalid request
    ServerError,             # Server error
)

try:
    client.v2.get_highlight(999999)
except NotFoundError:
    print("Highlight not found")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
```

## AsyncReadwiseClient

The async client provides the same functionality with async/await support for non-blocking I/O.

::: readwise_sdk.client.AsyncReadwiseClient
    options:
      show_source: false
      members:
        - __init__
        - validate_token
        - v2
        - v3

### Usage

```python
import asyncio
from readwise_sdk import AsyncReadwiseClient

async def main():
    # Using environment variable
    async with AsyncReadwiseClient() as client:
        # Get highlights
        async for highlight in client.v2.list_highlights():
            print(highlight.text)

        # Get documents
        async for doc in client.v3.list_documents():
            print(doc.title)

asyncio.run(main())
```

### Concurrent Operations

The async client enables efficient concurrent requests:

```python
import asyncio
from readwise_sdk import AsyncReadwiseClient

async def main():
    async with AsyncReadwiseClient() as client:
        # Fetch multiple documents concurrently
        doc_ids = ["doc1", "doc2", "doc3"]
        tasks = [client.v3.get_document(doc_id) for doc_id in doc_ids]
        docs = await asyncio.gather(*tasks)

        for doc in docs:
            print(doc.title)

asyncio.run(main())
```

### Properties

The async client has the same `v2` and `v3` properties as the sync client, but they return async versions of the API clients:

- `client.v2` → `AsyncReadwiseV2Client`
- `client.v3` → `AsyncReadwiseV3Client`

All methods on these clients are async and return async iterators where appropriate.
