# Client

The `ReadwiseClient` is the main entry point for the SDK.

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
