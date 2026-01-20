"""Convenience interfaces for common Readwise integration patterns.

These modules provide higher-level abstractions tailored to specific use cases:

- highlight_push: Simplified highlight syncing (push highlights TO Readwise)
- document_import: Document importing with metadata extraction (pull from Reader)
- batch_sync: Efficient batch synchronization with state tracking
"""

from readwise_sdk.contrib.batch_sync import BatchSync, BatchSyncConfig, BatchSyncResult
from readwise_sdk.contrib.document_import import (
    DocumentImporter,
    ImportedDocument,
    ImportResult,
)
from readwise_sdk.contrib.highlight_push import (
    AsyncHighlightPusher,
    HighlightPusher,
    PushResult,
    SimpleHighlight,
)

__all__ = [
    # highlight_push
    "HighlightPusher",
    "AsyncHighlightPusher",
    "SimpleHighlight",
    "PushResult",
    # document_import
    "DocumentImporter",
    "ImportedDocument",
    "ImportResult",
    # batch_sync
    "BatchSync",
    "BatchSyncConfig",
    "BatchSyncResult",
]
