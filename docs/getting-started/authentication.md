# Authentication

## Getting Your API Key

1. Log in to [Readwise](https://readwise.io)
2. Go to [readwise.io/access_token](https://readwise.io/access_token)
3. Copy your access token

!!! note
    The same API key works for both the Readwise API (v2) and the Reader API (v3).

## Setting Up Authentication

### Environment Variable (Recommended)

Set the `READWISE_API_KEY` environment variable:

=== "Linux/macOS"
    ```bash
    export READWISE_API_KEY="your_api_key_here"
    ```

=== "Windows (PowerShell)"
    ```powershell
    $env:READWISE_API_KEY = "your_api_key_here"
    ```

=== ".env file"
    ```bash
    # .env
    READWISE_API_KEY=your_api_key_here
    ```

Then initialize the client without arguments:

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient()  # Reads from READWISE_API_KEY
```

### Direct Initialization

Pass the API key directly (useful for testing):

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient(api_key="your_api_key_here")
```

!!! warning
    Never commit API keys to version control. Use environment variables or secret management tools.

## Validating Your Token

Verify your API key is valid:

```python
from readwise_sdk import ReadwiseClient

client = ReadwiseClient()

if client.validate_token():
    print("Token is valid!")
else:
    print("Token is invalid")
```

## Context Manager

Use the client as a context manager for proper cleanup:

```python
from readwise_sdk import ReadwiseClient

with ReadwiseClient() as client:
    highlights = list(client.v2.list_highlights())
    print(f"Found {len(highlights)} highlights")
# Connection is automatically closed
```

## Next Steps

- [Quick Start](quickstart.md) - Start using the SDK
