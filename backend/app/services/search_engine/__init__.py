"""Abstract search engine adapter interface.

Defines the contract that any search engine backend must implement.
Currently backed by Meilisearch, but switching to Elasticsearch (or another
engine) requires only a new adapter class — the rest of the application
never imports a search-engine-specific client directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


# ── Index document model ──────────────────────────────────────────────

@dataclass
class SearchDocument:
    """A single indexed resource document."""

    # Unique ID within the index (e.g. "image_2d:42" or "three_d:abc-def")
    id: str

    # Core fields (mirror UnifiedResourceSummary)
    source_system: str
    source_id: str
    source_label: str
    title: str
    resource_type: str
    updated_at: str  # ISO-8601 string for sortability
    profile_key: str | None = None
    profile_label: str | None = None
    status: str = "unknown"
    preview_enabled: bool = False
    thumbnail_url: str | None = None

    # Extended fields (for filtering / display)
    resolution: str | None = None
    format: str | None = None
    era: str | None = None
    object_level: str | None = None
    main_person: str | None = None
    main_location: str | None = None

    # URLs needed for frontend rendering
    manifest_url: str = ""
    detail_url: str = ""

    # Cross-source relation anchor
    object_number: str | None = None

    # Generic metadata bag (forward-compatible with future fields)
    extra: dict[str, Any] = field(default_factory=dict)

    # Search-boosted content (aggregated text for full-text)
    search_text: str = ""


# ── Query model ───────────────────────────────────────────────────────

@dataclass
class SearchQuery:
    """Structured search query understood by all adapters."""

    q: str | None = None
    filter: dict[str, Any] = field(default_factory=dict)
    sort_by: str | None = None
    sort_order: str = "desc"
    skip: int = 0
    limit: int = 20
    facets: list[str] | None = None


@dataclass
class SearchResult:
    """A single search result returned by the adapter."""

    id: str
    score: float | None = None
    document: dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Paginated search response."""

    items: list[SearchResult]
    total: int
    facet_distribution: dict[str, dict[str, int]] = field(default_factory=dict)


# ── Abstract adapter ──────────────────────────────────────────────────

class SearchEngineAdapter(ABC):
    """Interface that every search-engine backend must implement."""

    @abstractmethod
    def index_document(self, doc: SearchDocument) -> None:
        """Index (create or update) a single document."""
        ...

    @abstractmethod
    def index_documents(self, docs: list[SearchDocument]) -> None:
        """Batch-index multiple documents."""
        ...

    @abstractmethod
    def delete_document(self, doc_id: str) -> None:
        """Remove a document from the index by its ID."""
        ...

    @abstractmethod
    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """Retrieve a single document by ID, or None."""
        ...

    @abstractmethod
    def search(self, query: SearchQuery) -> SearchResponse:
        """Execute a structured search and return results."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Return the total number of indexed documents."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all documents from the index."""
        ...

    @abstractmethod
    def health(self) -> bool:
        """Return True if the search engine is reachable."""
        ...

    @abstractmethod
    def create_index_if_missing(self) -> None:
        """Ensure the index (and its settings) exist."""
        ...
