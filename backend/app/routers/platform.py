"""Unified platform directory — routes for cross-system resource browsing.

Queries are routed through the Meilisearch-backed unified index when available,
with automatic fallback to per-adapter in-memory filtering.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    PaginatedUnifiedResourceList,
    UnifiedResourceDetail,
    UnifiedResourceSourceSummary,
    UnifiedResourceSummary,
)
from ..platform.registry import registry
from ..services.search_engine.engine import get_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/sources", response_model=list[UnifiedResourceSourceSummary])
def get_sources(db: Session = Depends(get_db)):
    return [adapter.list_source_summary(db) for adapter in registry.all()]


@router.get("/resources", response_model=PaginatedUnifiedResourceList)
def get_resources(
    q: str | None = None,
    status: str | None = None,
    resource_type: str | None = None,
    profile_key: str | None = None,
    preview_enabled: bool | None = None,
    source_system: str | None = None,
    skip: int = 0,
    limit: int = 20,
    sort_by: str = Query("updated_at", description="Sort field: updated_at, title, status"),
    sort_order: str = Query("desc", description="Sort direction: asc, desc"),
    db: Session = Depends(get_db),
):
    """List unified resources.

    When the Meilisearch engine is healthy, queries are handled by the
    search engine (supports full-text search, faceted filtering, sorting).
    Falls back to per-adapter in-memory filtering if the engine is down.
    """
    engine = get_engine()

    if engine and engine.health():
        return _search_via_engine(
            engine, q, status, resource_type, profile_key,
            preview_enabled, source_system, skip, limit,
            sort_by, sort_order,
        )

    # Fallback: original per-adapter approach
    logger.info("Search engine unavailable — falling back to adapter-based filtering")
    return _search_via_adapters(
        q, status, resource_type, profile_key,
        preview_enabled, source_system, skip, limit,
        sort_by, sort_order, db,
    )


def _search_via_engine(
    engine,
    q: str | None,
    status: str | None,
    resource_type: str | None,
    profile_key: str | None,
    preview_enabled: bool | None,
    source_system: str | None,
    skip: int,
    limit: int,
    sort_by: str,
    sort_order: str,
) -> PaginatedUnifiedResourceList:
    from ..services.search_engine import SearchQuery

    # Build filter dict from non-None query params
    filters: dict = {}
    if status is not None:
        filters["status"] = status.split(",") if "," in status else status
    if resource_type is not None:
        filters["resource_type"] = resource_type
    if profile_key is not None:
        filters["profile_key"] = profile_key
    if preview_enabled is not None:
        filters["preview_enabled"] = preview_enabled
    if source_system is not None:
        filters["source_system"] = source_system

    meili_sort = sort_by if sort_by in ("updated_at", "title", "status") else None

    query = SearchQuery(
        q=q or "",
        filter=filters,
        sort_by=meili_sort,
        sort_order=sort_order,
        skip=skip,
        limit=limit,
    )

    response = engine.search(query)

    items: list[UnifiedResourceSummary] = []
    for hit in response.items:
        d = hit.document
        items.append(UnifiedResourceSummary(
            id=d.get("id", ""),
            source_system=d.get("source_system", ""),
            source_id=d.get("source_id", ""),
            source_label=d.get("source_label", ""),
            title=d.get("title", ""),
            resource_type=d.get("resource_type", ""),
            profile_key=d.get("profile_key"),
            profile_label=d.get("profile_label"),
            status=d.get("status", "unknown"),
            preview_enabled=d.get("preview_enabled", False),
            manifest_url=d.get("manifest_url", ""),
            detail_url=d.get("detail_url", ""),
            thumbnail_url=d.get("thumbnail_url"),
            updated_at=d.get("updated_at"),
            resolution=d.get("resolution"),
            format=d.get("format"),
            era=d.get("era"),
            object_level=d.get("object_level"),
            main_person=d.get("main_person"),
            main_location=d.get("main_location"),
        ))

    return PaginatedUnifiedResourceList(
        total=response.total,
        page=(skip // max(limit, 1)) + 1,
        size=limit,
        items=items,
    )


def _search_via_adapters(
    q: str | None,
    status: str | None,
    resource_type: str | None,
    profile_key: str | None,
    preview_enabled: bool | None,
    source_system: str | None,
    skip: int,
    limit: int,
    sort_by: str,
    sort_order: str,
    db: Session,
) -> PaginatedUnifiedResourceList:
    """Original adapter-based search — kept as fallback."""
    adapters = [registry.get(source_system)] if source_system else list(registry.all())
    if source_system and adapters[0] is None:
        return PaginatedUnifiedResourceList(total=0, page=_page_of(skip, limit), size=limit, items=[])

    resources: list[UnifiedResourceSummary] = []
    for adapter in adapters:
        if adapter is None:
            continue
        resources.extend(
            adapter.list_unified_resources(
                db,
                q=q,
                status=status,
                resource_type=resource_type,
                profile_key=profile_key,
                preview_enabled=preview_enabled,
            )
        )

    # Apply sorting
    sort_key_map = {
        "updated_at": lambda item: item.updated_at,
        "title": lambda item: (item.title or "").lower(),
        "status": lambda item: item.status or "",
    }
    sort_key = sort_key_map.get(sort_by)
    if sort_key is None:
        allowed = ", ".join(sorted(sort_key_map))
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort_by '{sort_by}'. Allowed: {allowed}",
        )
    if sort_order not in ("asc", "desc"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort_order '{sort_order}'. Allowed: asc, desc",
        )
    resources.sort(key=sort_key, reverse=(sort_order != "asc"))

    total = len(resources)
    page = _page_of(skip, limit)
    paged = resources[skip : skip + limit]
    return PaginatedUnifiedResourceList(total=total, page=page, size=limit, items=paged)


# ── Detail endpoints (unchanged — always use adapter) ────────────────

def _get_resource_detail(
    source_system: str,
    source_id: str,
    db: Session,
) -> UnifiedResourceDetail:
    adapter = registry.get(source_system)
    if adapter is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    try:
        return adapter.get_unified_resource_by_source(source_system, source_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/resources/{source_system}/{source_id}", response_model=UnifiedResourceDetail)
def get_resource_by_source(
    source_system: str,
    source_id: str,
    format: str | None = Query(None, description="Output format: 'dc' for Dublin Core"),
    db: Session = Depends(get_db),
):
    detail = _get_resource_detail(source_system, source_id, db)
    if format == "dc":
        from ..services.metadata_standards import from_unified_resource_detail
        return from_unified_resource_detail(detail)
    return detail


@router.get("/resources/{resource_id}", response_model=UnifiedResourceDetail, deprecated=True)
def get_resource(resource_id: str, db: Session = Depends(get_db)):
    source_system, separator, source_id = resource_id.partition(":")
    if not separator:
        raise HTTPException(status_code=400, detail="Unknown unified resource id")
    return _get_resource_detail(source_system, source_id, db)


# ── Search engine management ────────────────────────────────────────


@router.post("/reindex")
def reindex_resources(db: Session = Depends(get_db)):
    """Force a full reindex of all resources from all platform sources.

    The search engine will be cleared and re-populated from scratch.
    Returns the number of documents indexed.
    """
    from ..services.search_engine.engine import get_engine, seed_index_from_adapters

    engine = get_engine()
    if engine is None:
        raise HTTPException(status_code=503, detail="Search engine not available")

    engine.clear()
    seed_index_from_adapters(db)
    count = engine.count()
    return {"status": "ok", "indexed_count": count, "engine": "meilisearch"}


@router.get("/search-health")
def search_health():
    """Check if the search engine is healthy and return index stats."""
    from ..services.search_engine.engine import get_engine

    engine = get_engine()
    if engine is None:
        return {"healthy": False, "detail": "Search engine not initialized"}

    try:
        ok = engine.health()
        count = engine.count() if ok else 0
        return {"healthy": ok, "doc_count": count, "engine": "meilisearch"}
    except Exception as exc:
        return {"healthy": False, "detail": str(exc)}


@router.get("/related", response_model=PaginatedUnifiedResourceList)
def get_related_resources(
    object_number: str = Query(..., description="文物号，如 G12345"),
    exclude_source: str | None = Query(None, description="排除的来源系统"),
    exclude_id: str | None = Query(None, description="排除的资源 ID"),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """查找与指定文物号关联的所有跨来源资源（hasRepresentation）。

    优先通过 Meilisearch 的 object_number 过滤，降级到适配器查询。
    """
    from ..services.search_engine.engine import get_engine
    from ..services.search_engine import SearchQuery

    engine = get_engine()
    if engine and engine.health():
        filters = {"object_number": object_number}
        if exclude_source:
            filters["source_system"] = exclude_source
        query = SearchQuery(
            filter=filters,
            skip=skip,
            limit=limit,
        )
        response = engine.search(query)
        items: list[UnifiedResourceSummary] = []
        for hit in response.items:
            d = hit.document
            if exclude_id and d.get("source_id") == exclude_id:
                continue
            items.append(UnifiedResourceSummary(
                id=d.get("id", ""),
                source_system=d.get("source_system", ""),
                source_id=d.get("source_id", ""),
                source_label=d.get("source_label", ""),
                title=d.get("title", ""),
                resource_type=d.get("resource_type", ""),
                profile_key=d.get("profile_key"),
                profile_label=d.get("profile_label"),
                status=d.get("status", "unknown"),
                preview_enabled=d.get("preview_enabled", False),
                manifest_url=d.get("manifest_url", ""),
                detail_url=d.get("detail_url", ""),
                thumbnail_url=d.get("thumbnail_url"),
                updated_at=d.get("updated_at"),
            ))
        return PaginatedUnifiedResourceList(
            total=response.total,
            page=(skip // max(limit, 1)) + 1,
            size=limit,
            items=items,
        )

    # Fallback: query each adapter (uses db metadata profile fields)
    all_items: list[UnifiedResourceSummary] = []
    for adapter in registry.all():
        if adapter is None:
            continue
        try:
            resources = adapter.list_unified_resources(db, q=object_number)
            for r in resources:
                # Filter by object_number in profile metadata
                try:
                    detail = adapter.get_unified_resource_by_source(
                        r.source_system, r.source_id, db
                    )
                    record = (detail.source_record or {}).get("profile", {}) or {}
                    if isinstance(record, dict) and record.get("object_number") == object_number:
                        all_items.append(r)
                except Exception:
                    continue
        except Exception:
            continue

    if exclude_source:
        all_items = [r for r in all_items if r.source_system != exclude_source]
    if exclude_id:
        all_items = [r for r in all_items if r.source_id != exclude_id]

    return PaginatedUnifiedResourceList(
        total=len(all_items),
        page=(skip // max(limit, 1)) + 1,
        size=limit,
        items=all_items[skip:skip + limit],
    )


def _page_of(skip: int, limit: int) -> int:
    return (skip // max(limit, 1)) + 1
