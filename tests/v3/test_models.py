"""Tests for Readwise Reader API v3 models."""

from datetime import UTC, datetime

from readwise_sdk.v3.models import (
    CreateDocumentResult,
    Document,
    DocumentCategory,
    DocumentCreate,
    DocumentLocation,
    DocumentTag,
    DocumentUpdate,
)


class TestDocumentTag:
    """Tests for DocumentTag model."""

    def test_basic_tag(self) -> None:
        """Test basic tag creation."""
        tag = DocumentTag(key="favorite", name="Favorite")
        assert tag.key == "favorite"
        assert tag.name == "Favorite"


class TestDocument:
    """Tests for Document model."""

    def test_minimal_document(self) -> None:
        """Test document with minimal data."""
        doc = Document(id="abc123", url="https://example.com/article")
        assert doc.id == "abc123"
        assert doc.url == "https://example.com/article"
        assert doc.title is None
        assert doc.tags == []

    def test_full_document(self) -> None:
        """Test document with all fields."""
        data = {
            "id": "doc123",
            "url": "https://readwise.io/reader/doc123",
            "source_url": "https://example.com/article",
            "title": "Great Article",
            "author": "John Doe",
            "source": "web",
            "category": "article",
            "location": "new",
            "tags": ["tech", "ai"],
            "site_name": "Example Blog",
            "word_count": 1500,
            "reading_time": 7,
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-16T08:00:00Z",
            "summary": "A summary of the article",
            "reading_progress": 0.5,
        }
        doc = Document.model_validate(data)

        assert doc.id == "doc123"
        assert doc.title == "Great Article"
        assert doc.author == "John Doe"
        assert doc.category == DocumentCategory.ARTICLE
        assert doc.location == DocumentLocation.NEW
        assert doc.tags == ["tech", "ai"]
        assert doc.word_count == 1500
        assert doc.reading_progress == 0.5

    def test_document_with_dict_tags(self) -> None:
        """Test document with tags as dict objects."""
        data = {
            "id": "doc123",
            "url": "https://example.com",
            "tags": [{"name": "important"}, {"name": "work"}],
        }
        doc = Document.model_validate(data)
        assert doc.tags == ["important", "work"]

    def test_document_invalid_category(self) -> None:
        """Test document with invalid category."""
        data = {"id": "doc123", "url": "https://example.com", "category": "unknown"}
        doc = Document.model_validate(data)
        assert doc.category is None

    def test_document_invalid_location(self) -> None:
        """Test document with invalid location."""
        data = {"id": "doc123", "url": "https://example.com", "location": "unknown"}
        doc = Document.model_validate(data)
        assert doc.location is None

    def test_document_datetime_parsing(self) -> None:
        """Test datetime parsing from various formats."""
        data = {
            "id": "doc123",
            "url": "https://example.com",
            "created_at": "2024-01-15T10:30:00+00:00",
            "saved_at": "2024-01-15T10:30:00Z",
        }
        doc = Document.model_validate(data)
        assert doc.created_at is not None
        assert doc.saved_at is not None


class TestDocumentCreate:
    """Tests for DocumentCreate model."""

    def test_minimal_create(self) -> None:
        """Test minimal document creation."""
        create = DocumentCreate(url="https://example.com/article")
        api_dict = create.to_api_dict()

        assert api_dict == {"url": "https://example.com/article"}

    def test_full_create(self) -> None:
        """Test full document creation."""
        create = DocumentCreate(
            url="https://example.com/article",
            html="<html><body>Content</body></html>",
            should_clean_html=True,
            title="My Article",
            author="Author Name",
            summary="A brief summary",
            published_date=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            location=DocumentLocation.LATER,
            category=DocumentCategory.ARTICLE,
            saved_using="my-app",
            tags=["tech", "programming"],
            notes="Important article",
        )
        api_dict = create.to_api_dict()

        assert api_dict["url"] == "https://example.com/article"
        assert api_dict["html"] == "<html><body>Content</body></html>"
        assert api_dict["should_clean_html"] is True
        assert api_dict["title"] == "My Article"
        assert api_dict["location"] == "later"
        assert api_dict["category"] == "article"
        assert api_dict["tags"] == ["tech", "programming"]


class TestDocumentUpdate:
    """Tests for DocumentUpdate model."""

    def test_partial_update(self) -> None:
        """Test partial document update."""
        update = DocumentUpdate(title="New Title")
        api_dict = update.to_api_dict()

        assert api_dict == {"title": "New Title"}

    def test_location_update(self) -> None:
        """Test location update."""
        update = DocumentUpdate(location=DocumentLocation.ARCHIVE)
        api_dict = update.to_api_dict()

        assert api_dict == {"location": "archive"}

    def test_tags_update(self) -> None:
        """Test tags update."""
        update = DocumentUpdate(tags=["new-tag", "another"])
        api_dict = update.to_api_dict()

        assert api_dict == {"tags": ["new-tag", "another"]}


class TestCreateDocumentResult:
    """Tests for CreateDocumentResult model."""

    def test_result(self) -> None:
        """Test result parsing."""
        data = {"id": "doc123", "url": "https://readwise.io/reader/doc123"}
        result = CreateDocumentResult.model_validate(data)

        assert result.id == "doc123"
        assert result.url == "https://readwise.io/reader/doc123"
