from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import ThreeDAsset
from ..schemas import UnifiedResourceDetail, UnifiedResourceSourceSummary, UnifiedResourceSummary
from ..services.three_d_detail import build_three_d_detail_response
from ..services.three_d_metadata import PROFILE_DEFINITIONS, SOURCE_LABEL, SOURCE_SYSTEM, build_three_d_metadata_layers
from .base import PlatformSourceAdapter
from .registry import registry

RESOURCE_TYPE = "three_d_package"


def _resource_id(asset_id: int) -> str:
    return f"{SOURCE_SYSTEM}:{asset_id}"


def _source_last_synced_at(db: Session) -> datetime:
    latest_created_at = db.query(func.max(ThreeDAsset.created_at)).scalar()
    if latest_created_at is None:
        return datetime.now(timezone.utc)
    return latest_created_at


def _asset_file_records(asset: ThreeDAsset) -> list[dict[str, object]]:
    return [
        {
            "role": file_record.role,
            "role_label": file_record.role_label,
            "filename": file_record.filename,
            "actual_filename": file_record.actual_filename,
            "file_path": file_record.file_path,
            "file_size": file_record.file_size,
            "mime_type": file_record.mime_type,
            "is_primary": file_record.is_primary,
            "sort_order": file_record.sort_order,
        }
        for file_record in asset.files
    ]


def _asset_preview_enabled(asset: ThreeDAsset, layers: dict[str, object]) -> bool:
    core = layers.get("core") if isinstance(layers, dict) else {}
    if isinstance(core, dict):
        status = str(core.get("web_preview_status") or asset.web_preview_status or "disabled")
        is_web_preview = core.get("is_web_preview")
        if is_web_preview is not None:
            return bool(is_web_preview) and status == "ready"
    return bool(asset.is_web_preview and asset.web_preview_status == "ready" and asset.status == "ready")


def list_source_summary(db: Session) -> UnifiedResourceSourceSummary:
    resource_count = db.query(ThreeDAsset).count()
    return UnifiedResourceSourceSummary(
        source_system=SOURCE_SYSTEM,
        source_label=SOURCE_LABEL,
        resource_type=RESOURCE_TYPE,
        resource_count=resource_count,
        status="healthy",
        healthy=True,
        last_synced_at=_source_last_synced_at(db) if resource_count else None,
        entrypoint="/api/three-d/resources",
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
    query = db.query(ThreeDAsset)
    if status:
        query = query.filter(ThreeDAsset.status == status)
    if resource_type:
        query = query.filter(ThreeDAsset.resource_type == resource_type)

    assets = query.order_by(ThreeDAsset.created_at.desc(), ThreeDAsset.id.desc()).all()
    resources: list[UnifiedResourceSummary] = []
    normalized_query = q.strip().lower() if q else None
    normalized_profile_key = profile_key.strip() if profile_key else None
    if normalized_profile_key and normalized_profile_key not in PROFILE_DEFINITIONS:
        return []

    for asset in assets:
        file_records = _asset_file_records(asset)
        layers = build_three_d_metadata_layers(
            asset_id=asset.id,
            asset_filename=asset.filename,
            asset_file_path=asset.file_path,
            asset_file_size=asset.file_size,
            asset_mime_type=asset.mime_type,
            asset_status=asset.status,
            asset_resource_type=asset.resource_type,
            asset_created_at=asset.created_at,
            metadata=asset.metadata_info or {},
            file_records=file_records,
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
                layers["core"].get("version_label") or "",
                layers["core"].get("web_preview_status") or "",
                layers["core"].get("resource_group") or "",
                layers.get("technical", {}).get("role_summary") or "",
            ]
            search_tokens.extend(str(value) for value in (layers.get("management") or {}).values())
            search_tokens.extend(str(value) for value in (layers.get("collection") or {}).values())
            search_tokens.extend(str(value) for value in (layers.get("technical") or {}).values())
            profile_fields = (layers.get("profile") or {}).get("fields") or {}
            search_tokens.extend(str(value) for value in profile_fields.values())
            search_tokens.extend(str(value) for value in (layers.get("preservation") or {}).values())
            search_tokens.extend(str(value) for value in (layers.get("raw_metadata") or {}).values())
            search_blob = " ".join(search_tokens).lower()
            if normalized_query not in search_blob:
                continue

        asset_preview_enabled = _asset_preview_enabled(asset, layers)
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
                manifest_url=f"/api/three-d/resources/{asset.id}" if asset_preview_enabled else f"/api/three-d/resources/{asset.id}",
                detail_url=f"/api/platform/resources/{_resource_id(asset.id)}",
                updated_at=asset.created_at,
            )
        )
    return resources


def get_unified_resource(resource_id: str, db: Session) -> UnifiedResourceDetail:
    source_system, separator, source_id = resource_id.partition(":")
    if not separator or source_system != SOURCE_SYSTEM or not source_id.isdigit():
        raise ValueError("Unknown unified resource id")

    asset = db.query(ThreeDAsset).filter(ThreeDAsset.id == int(source_id)).first()
    if asset is None:
        raise LookupError("Resource not found")

    detail = build_three_d_detail_response(asset)
    layers = detail.metadata_layers

    return UnifiedResourceDetail(
        id=_resource_id(asset.id),
        source_system=SOURCE_SYSTEM,
        source_id=str(asset.id),
        source_label=SOURCE_LABEL,
        title=str(layers.get("core", {}).get("title") or asset.filename),
        resource_type=asset.resource_type or RESOURCE_TYPE,
        profile_key=str((layers.get("core") or {}).get("profile_key") or "other"),
        profile_label=str((layers.get("core") or {}).get("profile_label") or PROFILE_DEFINITIONS[str((layers.get("core") or {}).get("profile_key") or "other")]["label"]),
        status=asset.status,
        preview_enabled=_asset_preview_enabled(asset, layers),
        manifest_url=f"/api/three-d/resources/{asset.id}",
        detail_url=f"/api/three-d/resources/{asset.id}",
        updated_at=asset.created_at,
        source_detail_url=f"/api/three-d/resources/{asset.id}",
        source_record=None,
    )


class ThreeDSourceAdapter(PlatformSourceAdapter):
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


registry.register(ThreeDSourceAdapter())
