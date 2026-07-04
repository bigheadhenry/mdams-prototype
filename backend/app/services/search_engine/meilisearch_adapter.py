"""Meilisearch adapter — concrete implementation of SearchEngineAdapter."""

from __future__ import annotations

import logging
from typing import Any

import meilisearch
from meilisearch.errors import MeilisearchApiError

from app import config
from . import (
    SearchDocument,
    SearchEngineAdapter,
    SearchQuery,
    SearchResponse,
    SearchResult,
)

logger = logging.getLogger(__name__)

# Index name for unified resource documents
INDEX_NAME = "mdams_resources"

# Sortable attributes (must match fields in SearchDocument)
SORTABLE_ATTRIBUTES = [
    "updated_at",
    "title",
    "status",
]

# Filterable attributes (for faceted search)
FILTERABLE_ATTRIBUTES = [
    "source_system",
    "resource_type",
    "profile_key",
    "status",
    "preview_enabled",
    "era",
    "object_level",
    "main_person",
    "main_location",
    "format",
    "object_number",
]

# Searchable attributes (full-text fields)
SEARCHABLE_ATTRIBUTES = [
    "title",
    "search_text",
    "source_label",
    "profile_label",
    "resolution",
    "format",
    "era",
    "main_person",
    "main_location",
]


def _client() -> meilisearch.Client:
    """Return a configured Meilisearch client."""
    return meilisearch.Client(config.MEILI_URL, config.MEILI_MASTER_KEY)


class MeilisearchAdapter(SearchEngineAdapter):
    """Meilisearch backend for the unified search engine."""

    def __init__(self) -> None:
        self._client = _client()

    # ── Index management ──────────────────────────────────────────────

    def create_index_if_missing(self) -> None:
        try:
            # get_index raises if it doesn't exist
            self._client.get_index(INDEX_NAME)
            logger.info("Index '%s' already exists", INDEX_NAME)
        except MeilisearchApiError:
            logger.info("Creating index '%s'...", INDEX_NAME)
            self._client.create_index(INDEX_NAME, {"primaryKey": "id"})

        # Ensure sortable / filterable / searchable attributes
        index = self._client.index(INDEX_NAME)

        current_settings = index.get_settings()
        updates: dict[str, Any] = {}

        if current_settings.get("sortableAttributes") != SORTABLE_ATTRIBUTES:
            updates["sortableAttributes"] = SORTABLE_ATTRIBUTES
        if current_settings.get("filterableAttributes") != FILTERABLE_ATTRIBUTES:
            updates["filterableAttributes"] = FILTERABLE_ATTRIBUTES
        if current_settings.get("searchableAttributes") != SEARCHABLE_ATTRIBUTES:
            updates["searchableAttributes"] = SEARCHABLE_ATTRIBUTES

        if updates:
            index.update_settings(updates)
            logger.info("Updated index settings: %s", list(updates))

    # ── Document operations ───────────────────────────────────────────

    def index_document(self, doc: SearchDocument) -> None:
        self.index_documents([doc])

    def index_documents(self, docs: list[SearchDocument]) -> None:
        if not docs:
            return
        payload = [_doc_to_dict(d) for d in docs]
        resp = self._client.index(INDEX_NAME).add_documents(payload)
        logger.debug(
            "Indexed %d docs (task uid=%s, status=%s)",
            len(docs), resp.task_uid, resp.status,
        )

    def delete_document(self, doc_id: str) -> None:
        self._client.index(INDEX_NAME).delete_document(doc_id)
        logger.debug("Deleted doc '%s'", doc_id)

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        try:
            return self._client.index(INDEX_NAME).get_document(doc_id)
        except MeilisearchApiError:
            return None

    # ── Search ────────────────────────────────────────────────────────

    def search(self, query: SearchQuery) -> SearchResponse:
        index = self._client.index(INDEX_NAME)
        meili_params: dict[str, Any] = {
            "limit": query.limit,
            "offset": query.skip,
        }

        if query.q:
            meili_params["q"] = query.q
        else:
            meili_params["q"] = ""  # match all

        if query.sort_by:
            direction = "asc" if query.sort_order == "asc" else "desc"
            meili_params["sort"] = [f"{query.sort_by}:{direction}"]

        # Build filter expression from structured filters
        filter_expr = _build_filter_expression(query.filter)
        if filter_expr:
            meili_params["filter"] = filter_expr

        if query.facets:
            meili_params["facets"] = query.facets

        result = index.search(**meili_params)

        items = [
            SearchResult(
                id=h["id"],
                score=h.get("_rankingScore"),
                document=h,
            )
            for h in result.get("hits", [])
        ]

        facet_dist: dict[str, dict[str, int]] = {}
        for facet_key, facet_values in (result.get("facetDistribution") or {}).items():
            facet_dist[facet_key] = dict(facet_values)

        return SearchResponse(
            items=items,
            total=result.get("total", 0),
            facet_distribution=facet_dist,
        )

    def count(self) -> int:
        index = self._client.index(INDEX_NAME)
        stats = index.get_stats()
        return stats.number_of_documents

    def clear(self) -> None:
        self._client.index(INDEX_NAME).delete_all_documents()
        logger.info("Cleared all documents from '%s'", INDEX_NAME)

    def health(self) -> bool:
        try:
            self._client.health()
            return True
        except Exception:
            return False


# ── Helpers ───────────────────────────────────────────────────────────

def _doc_to_dict(doc: SearchDocument) -> dict[str, Any]:
    """Convert a SearchDocument to a flat dict for Meilisearch."""
    d: dict[str, Any] = {
        "id": doc.id,
        "source_system": doc.source_system,
        "source_id": doc.source_id,
        "source_label": doc.source_label,
        "title": doc.title,
        "resource_type": doc.resource_type,
        "profile_key": doc.profile_key,
        "profile_label": doc.profile_label,
        "status": doc.status,
        "preview_enabled": doc.preview_enabled,
        "thumbnail_url": doc.thumbnail_url,
        "updated_at": doc.updated_at,
        "manifest_url": doc.manifest_url,
        "detail_url": doc.detail_url,
        "object_number": doc.object_number,
        "resolution": doc.resolution,
        "format": doc.format,
        "era": doc.era,
        "object_level": doc.object_level,
        "main_person": doc.main_person,
        "main_location": doc.main_location,
        "search_text": doc.search_text,
    }
    d.update(doc.extra)
    return d


def _build_filter_expression(filters: dict[str, Any]) -> str | None:
    """Build a Meilisearch filter expression from a dict of field:value pairs.

    Supports simple equality and list-based IN filters.
    Example: {"source_system": "image_2d", "status": ["active", "draft"]}
    → "(source_system = image_2d) AND (status IN [active, draft])"
    """
    parts: list[str] = []
    for key, value in filters.items():
        if value is None:
            continue
        if isinstance(value, list):
            if not value:
                continue
            quoted = ", ".join(_q(v) for v in value)
            parts.append(f"({key} IN [{quoted}])")
        elif isinstance(value, bool):
            parts.append(f"({key} = {str(value).lower()})")
        else:
            parts.append(f"({key} = {_q(value)})")
    if not parts:
        return None
    return " AND ".join(parts)


def _q(value: Any) -> str:
    """Quote a value for Meilisearch filter syntax."""
    s = str(value)
    if " " in s or "'" in s:
        s = s.replace("'", "\\'")
        return f"'{s}'"
    return f"'{s}'"
