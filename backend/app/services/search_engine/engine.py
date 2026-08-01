"""Search engine singleton and lifecycle."""

from __future__ import annotations

import logging

from .meilisearch_adapter import MeilisearchAdapter

logger = logging.getLogger(__name__)

_engine: MeilisearchAdapter | None = None


def get_engine() -> MeilisearchAdapter | None:
    """Return the shared search engine instance, or None if unavailable."""
    global _engine
    return _engine


def init_engine() -> None:
    """Initialize the search engine singleton.

    Called once at application startup.  If Meilisearch is unreachable the
    engine stays None and the platform router falls back to adapter-based
    filtering transparently.
    """
    global _engine
    try:
        adapter = MeilisearchAdapter()
        if adapter.health():
            adapter.create_index_if_missing()
            _engine = adapter
            logger.info("Search engine initialized (Meilisearch at %s)", "")
        else:
            logger.warning("Meilisearch unreachable — search engine disabled")
    except Exception as exc:
        logger.warning("Failed to initialize search engine: %s", exc)
        _engine = None


def seed_index_from_adapters(db_session) -> None:
    """Populate (or refresh) the search index from all platform adapters.

    Safe to call multiple times — existing documents are overwritten.
    """
    engine = get_engine()
    if engine is None:
        logger.warning("Cannot seed index — engine unavailable")
        return

    from ...platform.registry import registry
    from . import SearchDocument

    total = 0
    for adapter in registry.all():
        try:
            resources = adapter.list_unified_resources(
                db_session, q=None, status=None,
                resource_type=None, profile_key=None,
                preview_enabled=None,
            )
        except Exception as exc:
            logger.warning("Failed to list resources from %s: %s", adapter.source_system, exc)
            continue

        docs = []
        for r in resources:
            # Pre-compute search-boosted text for full-text matching
            search_parts = [
                r.title or "",
                r.source_label or "",
                r.profile_label or "",
                r.resource_type or "",
            ]
            search_text = " ".join(p for p in search_parts if p)

            doc = SearchDocument(
                # Meilisearch primary keys cannot contain ':'. Keep its
                # internal ID safe and preserve the public platform ID in the
                # document payload for API responses.
                id=f"{r.source_system}__{r.source_id}",
                source_system=r.source_system,
                source_id=r.source_id,
                source_label=r.source_label,
                title=r.title,
                resource_type=r.resource_type,
                profile_key=r.profile_key,
                profile_label=r.profile_label,
                status=r.status,
                preview_enabled=r.preview_enabled,
                thumbnail_url=r.thumbnail_url,
                updated_at=r.updated_at.isoformat() if hasattr(r.updated_at, 'isoformat') else str(r.updated_at),
                resolution=r.resolution,
                format=r.format,
                era=r.era,
                object_level=r.object_level,
                main_person=r.main_person,
                main_location=r.main_location,
                manifest_url=r.manifest_url,
                detail_url=r.detail_url,
                object_number=None,  # TODO: fetch from resource detail during reindex
                search_text=search_text,
                extra={"platform_id": r.id},
            )
            docs.append(doc)

        if docs:
            engine.index_documents(docs)
            total += len(docs)
            logger.info("Indexed %d docs from %s", len(docs), adapter.source_system)

    logger.info("Seed complete: %d total documents indexed", total)
