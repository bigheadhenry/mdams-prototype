from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (
    UnifiedResourceDetail,
    UnifiedResourceSourceSummary,
    UnifiedResourceSummary,
)
from ..platform.registry import registry

router = APIRouter(prefix="/platform", tags=["platform"])


@router.get("/sources", response_model=list[UnifiedResourceSourceSummary])
def get_sources(db: Session = Depends(get_db)):
    return [adapter.list_source_summary(db) for adapter in registry.all()]


@router.get("/resources", response_model=list[UnifiedResourceSummary])
def get_resources(
    q: str | None = None,
    status: str | None = None,
    resource_type: str | None = None,
    profile_key: str | None = None,
    preview_enabled: bool | None = None,
    source_system: str | None = None,
    db: Session = Depends(get_db),
):
    adapters = [registry.get(source_system)] if source_system else list(registry.all())
    if source_system and adapters[0] is None:
        return []
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
    return resources


@router.get("/resources/{resource_id}", response_model=UnifiedResourceDetail)
def get_resource(resource_id: str, db: Session = Depends(get_db)):
    source_system, separator, _source_id = resource_id.partition(":")
    if not separator:
        raise HTTPException(status_code=400, detail="Unknown unified resource id")
    adapter = registry.get(source_system)
    if adapter is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    try:
        return adapter.get_unified_resource(resource_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
