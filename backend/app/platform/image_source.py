from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import Asset
from ..schemas import (
    UnifiedResourceDetail,
    UnifiedResourceSourceSummary,
    UnifiedResourceSummary,
)
from ..services.asset_detail import build_asset_detail_response
from ..services.iiif_access import is_iiif_ready
from ..services.metadata_layers import PROFILE_DEFINITIONS, build_metadata_layers
from .base import PlatformSourceAdapter
from .registry import registry

SOURCE_SYSTEM = "image_2d"
SOURCE_LABEL = "二维影像子系统"
RESOURCE_TYPE = "image_2d_cultural_object"


def _resource_id(asset_id: int) -> str:
    return f"{SOURCE_SYSTEM}:{asset_id}"


def _source_last_synced_at(db: Session) -> datetime:
    latest_created_at = db.query(func.max(Asset.created_at)).scalar()
    if latest_created_at is None:
        return datetime.now(timezone.utc)
    return latest_created_at


def list_source_summary(db: Session) -> UnifiedResourceSourceSummary:
    resource_count = db.query(Asset).count()
    return UnifiedResourceSourceSummary(
        source_system=SOURCE_SYSTEM,
        source_label=SOURCE_LABEL,
        resource_type=RESOURCE_TYPE,
        resource_count=resource_count,
        status="healthy",
        healthy=True,
        last_synced_at=_source_last_synced_at(db) if resource_count else None,
        entrypoint="/api/assets",
    )


def list_unified_resources(
    db: Session,
    *,
    q: str | None = None,
    status: str | None = None,
    resource_type: str | None = None,
    profile_key: str | None = None,
    preview_enabled: bool | None = None,
) -> list[UnifiedResourceSummary]:
    return list_unified_resources_filtered(
        db,
        q=q,
        status=status,
        resource_type=resource_type,
        profile_key=profile_key,
        preview_enabled=preview_enabled,
    )


def list_unified_resources_filtered(
    db: Session,
    *,
    q: str | None = None,
    status: str | None = None,
    resource_type: str | None = None,
    profile_key: str | None = None,
    preview_enabled: bool | None = None,
) -> list[UnifiedResourceSummary]:
    normalized_profile_key = profile_key.strip() if profile_key else None
    if normalized_profile_key and normalized_profile_key not in PROFILE_DEFINITIONS:
        return []

    query = db.query(Asset)

    if status:
        query = query.filter(Asset.status == status)

    if resource_type:
        query = query.filter(Asset.resource_type == resource_type)

    assets = query.order_by(Asset.created_at.desc(), Asset.id.desc()).all()

    resources: list[UnifiedResourceSummary] = []
    normalized_query = q.strip().lower() if q else None
    for asset in assets:
        layers = build_metadata_layers(
            asset_id=asset.id,
            asset_filename=asset.filename,
            asset_file_path=asset.file_path,
            asset_file_size=asset.file_size,
            asset_mime_type=asset.mime_type,
            asset_status=asset.status,
            asset_resource_type=asset.resource_type,
            asset_created_at=asset.created_at,
            metadata=asset.metadata_info or {},
        )
        asset_profile_key = str((layers.get("core") or {}).get("profile_key") or "other")
        if normalized_profile_key and asset_profile_key != normalized_profile_key:
            continue

        if normalized_query:
            search_tokens = [
                str(asset.id),
                f"{SOURCE_SYSTEM}:{asset.id}",
                asset.filename or "",
                asset.file_path or "",
                asset.mime_type or "",
                layers["core"].get("title") or "",
                layers["core"].get("resource_type") or "",
                layers["core"].get("resource_type_label") or "",
                layers["core"].get("profile_label") or "",
            ]
            search_tokens.extend(str(value) for value in (layers.get("management") or {}).values())
            search_tokens.extend(str(value) for value in (layers.get("technical") or {}).values())
            profile_fields = (layers.get("profile") or {}).get("fields") or {}
            search_tokens.extend(str(value) for value in profile_fields.values())
            search_tokens.extend(str(value) for value in (layers.get("raw_metadata") or {}).values())
            search_blob = " ".join(search_tokens).lower()
            if normalized_query not in search_blob:
                continue

        asset_preview_enabled = is_iiif_ready(asset)
        if preview_enabled is not None and preview_enabled != asset_preview_enabled:
            continue
        resources.append(
            UnifiedResourceSummary(
                id=_resource_id(asset.id),
                source_system=SOURCE_SYSTEM,
                source_id=str(asset.id),
                source_label=SOURCE_LABEL,
                title=str(layers["core"].get("title") or asset.filename),
                resource_type=asset.resource_type or RESOURCE_TYPE,
                profile_key=asset_profile_key,
                profile_label=str((layers.get("core") or {}).get("profile_label") or PROFILE_DEFINITIONS[asset_profile_key]["label"]),
                status=asset.status,
                preview_enabled=asset_preview_enabled,
                manifest_url=f"/api/iiif/{asset.id}/manifest",
                detail_url=f"/api/platform/resources/{_resource_id(asset.id)}",
                updated_at=asset.created_at,
            )
        )
    return resources


def get_unified_resource(resource_id: str, db: Session) -> UnifiedResourceDetail:
    source_system, separator, source_id = resource_id.partition(":")
    if not separator or source_system != SOURCE_SYSTEM or not source_id.isdigit():
        raise ValueError("Unknown unified resource id")

    asset = db.query(Asset).filter(Asset.id == int(source_id)).first()
    if asset is None:
        raise LookupError("Resource not found")

    source_record = build_asset_detail_response(asset)
    preview_enabled = is_iiif_ready(asset)
    layers = build_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_created_at=asset.created_at,
        metadata=asset.metadata_info or {},
    )

    return UnifiedResourceDetail(
        id=_resource_id(asset.id),
        source_system=SOURCE_SYSTEM,
        source_id=str(asset.id),
        source_label=SOURCE_LABEL,
        title=str(layers["core"].get("title") or asset.filename),
        resource_type=asset.resource_type or RESOURCE_TYPE,
        profile_key=str((layers.get("core") or {}).get("profile_key") or "other"),
        profile_label=str((layers.get("core") or {}).get("profile_label") or PROFILE_DEFINITIONS[str((layers.get("core") or {}).get("profile_key") or "other")]["label"]),
        status=asset.status,
        preview_enabled=preview_enabled,
        manifest_url=f"/api/iiif/{asset.id}/manifest",
        detail_url=f"/api/assets/{asset.id}",
        updated_at=asset.created_at,
        source_detail_url=f"/api/assets/{asset.id}",
        source_record=source_record,
    )


class Image2DSourceAdapter(PlatformSourceAdapter):
    source_system = SOURCE_SYSTEM
    source_label = SOURCE_LABEL
    resource_type = RESOURCE_TYPE

    def list_source_summary(self, db: Session) -> UnifiedResourceSourceSummary:
        return list_source_summary(db)

    def list_unified_resources(
        self,
        db: Session,
        *,
        q: str | None = None,
        status: str | None = None,
        resource_type: str | None = None,
        profile_key: str | None = None,
        preview_enabled: bool | None = None,
    ) -> list[UnifiedResourceSummary]:
        return list_unified_resources(
            db,
            q=q,
            status=status,
            resource_type=resource_type,
            profile_key=profile_key,
            preview_enabled=preview_enabled,
        )

    def get_unified_resource(self, resource_id: str, db: Session) -> UnifiedResourceDetail:
        return get_unified_resource(resource_id, db)


registry.register(Image2DSourceAdapter())
