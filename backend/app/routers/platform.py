"""Unified platform directory — routes for cross-system resource browsing.

Queries are routed through the Meilisearch-backed unified index when available,
with automatic fallback to per-adapter in-memory filtering.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..permissions import CurrentUser, ensure_current_user, require_permission
from ..schemas import (
    PaginatedUnifiedResourceList,
    UnifiedResourceDetail,
    UnifiedResourceSourceSummary,
    UnifiedResourceSummary,
)
from ..platform.registry import registry
from ..services.search_engine.engine import get_engine
from ..services.resource_access import (
    assert_platform_resource_visible,
    can_access_platform_source,
    can_view_platform_resource,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/sources", response_model=list[UnifiedResourceSourceSummary])
def get_sources(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("platform.view")),
):
    current_user = ensure_current_user(user)
    summaries: list[UnifiedResourceSourceSummary] = []
    for adapter in registry.all():
        if not can_access_platform_source(adapter.source_system, current_user):
            continue
        visible_count = sum(
            can_view_platform_resource(item.source_system, item.source_id, db, current_user)
            for item in adapter.list_unified_resources(db)
        )
        summaries.append(adapter.list_source_summary(db).model_copy(update={"resource_count": visible_count}))
    return summaries


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
    user: CurrentUser = Depends(require_permission("platform.view")),
):
    """List unified resources.

    When the Meilisearch engine is healthy, queries are handled by the
    search engine (supports full-text search, faceted filtering, sorting).
    Falls back to per-adapter in-memory filtering if the engine is down.
    """
    current_user = ensure_current_user(user)
    # Direct service calls in contract tests do not run FastAPI's Query
    # coercion, so normalize descriptor defaults at this boundary too.
    sort_by = sort_by if isinstance(sort_by, str) else "updated_at"
    sort_order = sort_order if isinstance(sort_order, str) else "desc"
    engine = get_engine()

    if engine and engine.health():
        return _search_via_engine(
            engine, q, status, resource_type, profile_key,
            preview_enabled, source_system, skip, limit,
            sort_by, sort_order, db, current_user,
        )

    # Fallback: original per-adapter approach
    logger.info("Search engine unavailable — falling back to adapter-based filtering")
    return _search_via_adapters(
        q, status, resource_type, profile_key,
        preview_enabled, source_system, skip, limit,
        sort_by, sort_order, db, current_user,
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
    db: Session,
    user: CurrentUser,
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

    # Do not trust visibility fields in an index: old documents may predate the
    # access-policy schema and stale documents may outlive their database row.
    # Fetch the matching result set, resolve every hit against the authoritative
    # database policy, then paginate so both items and total are scope-correct.
    visible_documents: list[dict] = []
    raw_skip = 0
    batch_size = 200
    seen_ids: set[str] = set()
    while True:
        response = engine.search(SearchQuery(
            q=q or "",
            filter=filters,
            sort_by=meili_sort,
            sort_order=sort_order,
            skip=raw_skip,
            limit=batch_size,
        ))
        if not response.items:
            break
        for hit in response.items:
            document = hit.document
            document_id = str(document.get("id") or "")
            if document_id in seen_ids:
                continue
            seen_ids.add(document_id)
            hit_source = str(document.get("source_system") or "")
            hit_source_id = str(document.get("source_id") or "")
            if can_view_platform_resource(hit_source, hit_source_id, db, user):
                visible_documents.append(document)
        raw_skip += len(response.items)
        if raw_skip >= response.total:
            break

    total = len(visible_documents)
    page_documents = visible_documents[skip : skip + max(limit, 0)]
    items = [_summary_from_search_document(document) for document in page_documents]

    return PaginatedUnifiedResourceList(
        total=total,
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
    user: CurrentUser,
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
            item
            for item in adapter.list_unified_resources(
                db,
                q=q,
                status=status,
                resource_type=resource_type,
                profile_key=profile_key,
                preview_enabled=preview_enabled,
            )
            if can_view_platform_resource(item.source_system, item.source_id, db, user)
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
    user: CurrentUser,
) -> UnifiedResourceDetail:
    adapter = registry.get(source_system)
    if adapter is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    assert_platform_resource_visible(source_system, source_id, db, user)
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
    user: CurrentUser = Depends(require_permission("platform.view")),
):
    detail = _get_resource_detail(source_system, source_id, db, ensure_current_user(user))
    if format == "dc":
        from ..services.metadata_standards import from_unified_resource_detail
        return from_unified_resource_detail(detail)
    return detail


@router.get("/resources/{resource_id}", response_model=UnifiedResourceDetail, deprecated=True)
def get_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("platform.view")),
):
    source_system, separator, source_id = resource_id.partition(":")
    if not separator:
        raise HTTPException(status_code=400, detail="Unknown unified resource id")
    return _get_resource_detail(source_system, source_id, db, ensure_current_user(user))


def _summary_from_search_document(d: dict) -> UnifiedResourceSummary:
    return UnifiedResourceSummary(
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
    )


# ── Search engine management ────────────────────────────────────────


@router.post("/reindex")
def reindex_resources(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("system.manage")),
):
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
def search_health(
    user: CurrentUser = Depends(require_permission("platform.view")),
):
    """Check if the search engine is healthy and return index stats."""
    from ..services.search_engine.engine import get_engine

    engine = get_engine()
    if engine is None:
        return {"healthy": False, "detail": "Search engine not initialized"}

    try:
        ok = engine.health()
        current_user = ensure_current_user(user)
        count = engine.count() if ok and current_user.has_permission("system.manage") else None
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
    user: CurrentUser = Depends(require_permission("platform.view")),
):
    """查找与指定文物号关联的所有跨来源资源（hasRepresentation）。

    优先通过 Meilisearch 的 object_number 过滤，降级到适配器查询。
    """
    from ..services.search_engine.engine import get_engine
    from ..services.search_engine import SearchQuery

    current_user = ensure_current_user(user)
    engine = get_engine()
    if engine and engine.health():
        filters = {"object_number": object_number}
        visible_documents: list[dict] = []
        raw_skip = 0
        while True:
            response = engine.search(SearchQuery(filter=filters, skip=raw_skip, limit=200))
            if not response.items:
                break
            for hit in response.items:
                d = hit.document
                if exclude_source and str(d.get("source_system") or "") == exclude_source:
                    continue
                if exclude_id and str(d.get("source_id") or "") == exclude_id:
                    continue
                if can_view_platform_resource(
                    str(d.get("source_system") or ""),
                    str(d.get("source_id") or ""),
                    db,
                    current_user,
                ):
                    visible_documents.append(d)
            raw_skip += len(response.items)
            if raw_skip >= response.total:
                break
        items = [
            _summary_from_search_document(d)
            for d in visible_documents[skip : skip + max(limit, 0)]
        ]
        return PaginatedUnifiedResourceList(
            total=len(visible_documents),
            page=(skip // max(limit, 1)) + 1,
            size=limit,
            items=items,
        )

    # Fallback: query each adapter (uses db metadata profile fields)
    all_items: list[UnifiedResourceSummary] = []
    for adapter in registry.all():
        if adapter is None:
            continue
        if not can_access_platform_source(adapter.source_system, current_user):
            continue
        try:
            resources = adapter.list_unified_resources(db, q=object_number)
            for r in resources:
                if not can_view_platform_resource(r.source_system, r.source_id, db, current_user):
                    continue
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
