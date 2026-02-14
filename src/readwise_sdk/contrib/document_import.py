"""Document importing interface with metadata extraction.

Designed for sane_reader and similar projects that need to pull documents
FROM Readwise Reader with extracted metadata.

Example:
    from readwise_sdk import ReadwiseClient
    from readwise_sdk.contrib import DocumentImporter

    client = ReadwiseClient()
    importer = DocumentImporter(client)

    # Import a single document with full content
    doc = importer.import_document("doc_id_here", with_content=True)
    print(f"Title: {doc.title}")
    print(f"Clean text: {doc.clean_text[:200]}...")
    print(f"Domain: {doc.domain}")
    print(f"Reading time: {doc.reading_time_minutes} mins")

    # Import multiple documents
    results = importer.import_batch(["doc1", "doc2", "doc3"])
    for result in results:
        if result.success:
            print(f"Imported: {result.document.title}")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from readwise_sdk.v3.models import Document, DocumentCategory, DocumentLocation

if TYPE_CHECKING:
    from readwise_sdk.client import AsyncReadwiseClient, ReadwiseClient

# Average reading speed (words per minute)
WORDS_PER_MINUTE = 200


@dataclass
class ImportedDocument:
    """A document imported from Readwise Reader with extracted metadata."""

    # Core fields from Document
    id: str
    url: str
    title: str | None
    author: str | None
    category: DocumentCategory | None
    location: DocumentLocation | None
    tags: list[str]
    created_at: datetime | None
    updated_at: datetime | None

    # Content
    html_content: str | None = None
    clean_text: str | None = None

    # Extracted metadata
    domain: str | None = None
    word_count: int | None = None
    reading_time_minutes: int | None = None
    summary: str | None = None
    image_url: str | None = None

    # Reading progress
    reading_progress: float | None = None
    first_opened_at: datetime | None = None
    last_opened_at: datetime | None = None

    @classmethod
    def from_document(
        cls,
        doc: Document,
        *,
        extract_metadata: bool = True,
        clean_html: bool = True,
    ) -> ImportedDocument:
        """Create from a Document with optional metadata extraction."""
        imported = cls(
            id=doc.id,
            url=doc.url,
            title=doc.title,
            author=doc.author,
            category=doc.category,
            location=doc.location,
            tags=doc.tags,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            html_content=doc.content,
            summary=doc.summary,
            image_url=doc.image_url,
            reading_progress=doc.reading_progress,
            first_opened_at=doc.first_opened_at,
            last_opened_at=doc.last_opened_at,
            word_count=doc.word_count,
            reading_time_minutes=doc.reading_time,
        )

        # Extract domain from URL
        if extract_metadata and doc.url:
            imported.domain = _extract_domain(doc.url)

        # Clean HTML to text
        if clean_html and doc.content:
            imported.clean_text = _html_to_text(doc.content)

            # Calculate word count and reading time if not provided
            if extract_metadata and imported.clean_text:
                if imported.word_count is None:
                    imported.word_count = len(imported.clean_text.split())
                if imported.reading_time_minutes is None and imported.word_count:
                    imported.reading_time_minutes = max(1, imported.word_count // WORDS_PER_MINUTE)

        return imported


@dataclass
class ImportResult:
    """Result of importing a document."""

    success: bool
    document: ImportedDocument | None = None
    document_id: str | None = None
    error: str | None = None


def _extract_domain(url: str) -> str | None:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain or None
    except Exception:
        return None


def _html_to_text(html: str) -> str:
    """Convert HTML to clean text.

    Uses regex-based extraction for simplicity (no BeautifulSoup dependency).
    For more robust extraction, install beautifulsoup4.
    """
    try:
        # Try to use BeautifulSoup if available
        from bs4 import BeautifulSoup  # type: ignore[import-not-found]

        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)
    except ImportError:
        # Fallback to regex-based extraction
        # Remove script and style blocks
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.I)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.I)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Decode common HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')
        text = text.replace("&#39;", "'")

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()

    return text


class DocumentImporter:
    """Interface for importing documents from Readwise Reader.

    Provides:
    - Automatic HTML to text conversion
    - Metadata extraction (domain, word count, reading time)
    - Batch operations with individual error handling
    - Rate limit aware operations
    """

    def __init__(
        self,
        client: ReadwiseClient,
        *,
        extract_metadata: bool = True,
        clean_html: bool = True,
    ) -> None:
        """Initialize the document importer.

        Args:
            client: The Readwise client.
            extract_metadata: Extract domain, word count, etc.
            clean_html: Convert HTML content to clean text.
        """
        self._client = client
        self._extract_metadata = extract_metadata
        self._clean_html = clean_html

    def import_document(
        self,
        document_id: str,
        *,
        with_content: bool = True,
    ) -> ImportedDocument:
        """Import a single document with optional content.

        Args:
            document_id: The document ID.
            with_content: Whether to fetch HTML content.

        Returns:
            ImportedDocument with extracted metadata.

        Raises:
            NotFoundError: If the document doesn't exist.
        """
        doc = self._client.v3.get_document(document_id, with_content=with_content)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")
        return ImportedDocument.from_document(
            doc,
            extract_metadata=self._extract_metadata,
            clean_html=self._clean_html,
        )

    def import_batch(
        self,
        document_ids: list[str],
        *,
        with_content: bool = True,
    ) -> list[ImportResult]:
        """Import multiple documents.

        Each document is fetched independently - failures don't affect others.

        Args:
            document_ids: List of document IDs.
            with_content: Whether to fetch HTML content.

        Returns:
            List of ImportResults in the same order as input.
        """
        results: list[ImportResult] = []

        for doc_id in document_ids:
            try:
                imported = self.import_document(doc_id, with_content=with_content)
                results.append(
                    ImportResult(
                        success=True,
                        document=imported,
                        document_id=doc_id,
                    )
                )
            except Exception as e:
                results.append(
                    ImportResult(
                        success=False,
                        document_id=doc_id,
                        error=str(e),
                    )
                )

        return results

    def list_inbox(
        self,
        *,
        limit: int | None = None,
        with_content: bool = False,
    ) -> list[ImportedDocument]:
        """List inbox documents with optional metadata extraction.

        Args:
            limit: Maximum number of documents to return.
            with_content: Whether to fetch HTML content (slower).

        Returns:
            List of ImportedDocuments.
        """
        return self._list_location(DocumentLocation.NEW, limit=limit, with_content=with_content)

    def list_reading_list(
        self,
        *,
        limit: int | None = None,
        with_content: bool = False,
    ) -> list[ImportedDocument]:
        """List reading list documents with optional metadata extraction.

        Args:
            limit: Maximum number of documents to return.
            with_content: Whether to fetch HTML content (slower).

        Returns:
            List of ImportedDocuments.
        """
        return self._list_location(DocumentLocation.LATER, limit=limit, with_content=with_content)

    def list_archive(
        self,
        *,
        limit: int | None = None,
        with_content: bool = False,
    ) -> list[ImportedDocument]:
        """List archived documents with optional metadata extraction.

        Args:
            limit: Maximum number of documents to return.
            with_content: Whether to fetch HTML content (slower).

        Returns:
            List of ImportedDocuments.
        """
        return self._list_location(DocumentLocation.ARCHIVE, limit=limit, with_content=with_content)

    def _list_location(
        self,
        location: DocumentLocation,
        *,
        limit: int | None = None,
        with_content: bool = False,
    ) -> list[ImportedDocument]:
        """List documents from a specific location."""
        results = []
        for i, doc in enumerate(
            self._client.v3.list_documents(location=location, with_content=with_content)
        ):
            if limit and i >= limit:
                break
            results.append(
                ImportedDocument.from_document(
                    doc,
                    extract_metadata=self._extract_metadata,
                    clean_html=self._clean_html,
                )
            )
        return results

    def list_updated_since(
        self,
        since: datetime,
        *,
        limit: int | None = None,
        with_content: bool = False,
    ) -> list[ImportedDocument]:
        """List documents updated since a timestamp.

        Args:
            since: Only return documents updated after this time.
            limit: Maximum number of documents to return.
            with_content: Whether to fetch HTML content (slower).

        Returns:
            List of ImportedDocuments.
        """
        results = []
        for i, doc in enumerate(
            self._client.v3.list_documents(updated_after=since, with_content=with_content)
        ):
            if limit and i >= limit:
                break
            results.append(
                ImportedDocument.from_document(
                    doc,
                    extract_metadata=self._extract_metadata,
                    clean_html=self._clean_html,
                )
            )
        return results

    def save_url(self, url: str, **kwargs) -> str:
        """Save a URL to Readwise Reader.

        Args:
            url: The URL to save.
            **kwargs: Additional arguments passed to create_document.

        Returns:
            The document ID of the created document.
        """
        result = self._client.v3.save_url(url, **kwargs)
        return result.id


class AsyncDocumentImporter:
    """Async interface for importing documents from Readwise Reader.

    Provides the same functionality as DocumentImporter but with async/await
    support for use with async frameworks like FastAPI or aiohttp.

    Example:
        from readwise_sdk import AsyncReadwiseClient
        from readwise_sdk.contrib import AsyncDocumentImporter

        async with AsyncReadwiseClient() as client:
            importer = AsyncDocumentImporter(client)

            # Import a single document with full content
            doc = await importer.import_document("doc_id_here", with_content=True)
            print(f"Title: {doc.title}")
    """

    def __init__(
        self,
        client: AsyncReadwiseClient,
        *,
        extract_metadata: bool = True,
        clean_html: bool = True,
    ) -> None:
        """Initialize the async document importer.

        Args:
            client: The async Readwise client.
            extract_metadata: Extract domain, word count, etc.
            clean_html: Convert HTML content to clean text.
        """
        self._client = client
        self._extract_metadata = extract_metadata
        self._clean_html = clean_html

    async def import_document(
        self,
        document_id: str,
        *,
        with_content: bool = True,
    ) -> ImportedDocument:
        """Import a single document with optional content.

        Args:
            document_id: The document ID.
            with_content: Whether to fetch HTML content.

        Returns:
            ImportedDocument with extracted metadata.

        Raises:
            ValueError: If the document doesn't exist.
        """
        doc = await self._client.v3.get_document(document_id, with_content=with_content)
        if doc is None:
            raise ValueError(f"Document {document_id} not found")
        return ImportedDocument.from_document(
            doc,
            extract_metadata=self._extract_metadata,
            clean_html=self._clean_html,
        )

    async def import_batch(
        self,
        document_ids: list[str],
        *,
        with_content: bool = True,
    ) -> list[ImportResult]:
        """Import multiple documents.

        Each document is fetched independently - failures don't affect others.

        Args:
            document_ids: List of document IDs.
            with_content: Whether to fetch HTML content.

        Returns:
            List of ImportResults in the same order as input.
        """
        results: list[ImportResult] = []

        for doc_id in document_ids:
            try:
                imported = await self.import_document(doc_id, with_content=with_content)
                results.append(
                    ImportResult(
                        success=True,
                        document=imported,
                        document_id=doc_id,
                    )
                )
            except Exception as e:
                results.append(
                    ImportResult(
                        success=False,
                        document_id=doc_id,
                        error=str(e),
                    )
                )

        return results

    async def list_inbox(
        self,
        *,
        limit: int | None = None,
        with_content: bool = False,
    ) -> list[ImportedDocument]:
        """List inbox documents with optional metadata extraction.

        Args:
            limit: Maximum number of documents to return.
            with_content: Whether to fetch HTML content (slower).

        Returns:
            List of ImportedDocuments.
        """
        return await self._list_location(
            DocumentLocation.NEW, limit=limit, with_content=with_content
        )

    async def list_reading_list(
        self,
        *,
        limit: int | None = None,
        with_content: bool = False,
    ) -> list[ImportedDocument]:
        """List reading list documents with optional metadata extraction.

        Args:
            limit: Maximum number of documents to return.
            with_content: Whether to fetch HTML content (slower).

        Returns:
            List of ImportedDocuments.
        """
        return await self._list_location(
            DocumentLocation.LATER, limit=limit, with_content=with_content
        )

    async def list_archive(
        self,
        *,
        limit: int | None = None,
        with_content: bool = False,
    ) -> list[ImportedDocument]:
        """List archived documents with optional metadata extraction.

        Args:
            limit: Maximum number of documents to return.
            with_content: Whether to fetch HTML content (slower).

        Returns:
            List of ImportedDocuments.
        """
        return await self._list_location(
            DocumentLocation.ARCHIVE, limit=limit, with_content=with_content
        )

    async def _list_location(
        self,
        location: DocumentLocation,
        *,
        limit: int | None = None,
        with_content: bool = False,
    ) -> list[ImportedDocument]:
        """List documents from a specific location."""
        results = []
        i = 0
        async for doc in self._client.v3.list_documents(
            location=location, with_content=with_content
        ):
            if limit and i >= limit:
                break
            results.append(
                ImportedDocument.from_document(
                    doc,
                    extract_metadata=self._extract_metadata,
                    clean_html=self._clean_html,
                )
            )
            i += 1
        return results

    async def list_updated_since(
        self,
        since: datetime,
        *,
        limit: int | None = None,
        with_content: bool = False,
    ) -> list[ImportedDocument]:
        """List documents updated since a timestamp.

        Args:
            since: Only return documents updated after this time.
            limit: Maximum number of documents to return.
            with_content: Whether to fetch HTML content (slower).

        Returns:
            List of ImportedDocuments.
        """
        results = []
        i = 0
        async for doc in self._client.v3.list_documents(
            updated_after=since, with_content=with_content
        ):
            if limit and i >= limit:
                break
            results.append(
                ImportedDocument.from_document(
                    doc,
                    extract_metadata=self._extract_metadata,
                    clean_html=self._clean_html,
                )
            )
            i += 1
        return results

    async def save_url(self, url: str, **kwargs) -> str:
        """Save a URL to Readwise Reader.

        Args:
            url: The URL to save.
            **kwargs: Additional arguments passed to create_document.

        Returns:
            The document ID of the created document.
        """
        result = await self._client.v3.save_url(url, **kwargs)
        return result.id
