"""High-level manager classes for common Readwise workflows."""

from readwise_sdk.managers.async_managers import (
    AsyncBookManager,
    AsyncDocumentManager,
    AsyncHighlightManager,
    AsyncSyncManager,
)
from readwise_sdk.managers.books import BookManager
from readwise_sdk.managers.documents import DocumentManager
from readwise_sdk.managers.highlights import HighlightManager
from readwise_sdk.managers.sync import SyncManager, SyncState

__all__ = [
    # Sync managers
    "HighlightManager",
    "BookManager",
    "DocumentManager",
    "SyncManager",
    "SyncState",
    # Async managers
    "AsyncHighlightManager",
    "AsyncBookManager",
    "AsyncDocumentManager",
    "AsyncSyncManager",
]
