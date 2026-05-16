from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    PaginatedUnifiedResourceList,
    UnifiedResourceDetail,
    UnifiedResourceSourceSummary,
    UnifiedResourceSummary,
)
from ..platform.registry import registry

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
    db: Session = Depends(get_db),
):
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
    resources.sort(key=lambda item: item.updated_at, reverse=True)
    total = len(resources)
    page = _page_of(skip, limit)
    paged = resources[skip : skip + limit]
    return PaginatedUnifiedResourceList(total=total, page=page, size=limit, items=paged)


def _page_of(skip: int, limit: int) -> int:
    return (skip // max(limit, 1)) + 1


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
def get_resource_by_source(source_system: str, source_id: str, db: Session = Depends(get_db)):
    return _get_resource_detail(source_system, source_id, db)


@router.get("/resources/{resource_id}", response_model=UnifiedResourceDetail, deprecated=True)
def get_resource(resource_id: str, db: Session = Depends(get_db)):
    source_system, separator, source_id = resource_id.partition(":")
    if not separator:
        raise HTTPException(status_code=400, detail="Unknown unified resource id")
    return _get_resource_detail(source_system, source_id, db)
