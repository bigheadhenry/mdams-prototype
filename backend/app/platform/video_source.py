from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import VideoAsset
from ..schemas import (
    UnifiedResourceAction,
    UnifiedResourceDetail,
    UnifiedResourceSourceSummary,
    UnifiedResourceSummary,
)
from ..services.video_metadata import PROFILE_DEFINITIONS, build_video_metadata_layers
from .base import PlatformSourceAdapter
from .registry import registry

SOURCE_SYSTEM = "video"
SOURCE_LABEL = "视频子系统"
RESOURCE_TYPE = "video_cultural_object"


def _platform_id(asset_id: int) -> str:
    return f"{SOURCE_SYSTEM}:{asset_id}"


def _resource_detail_url(asset_id: int) -> str:
    return f"/api/platform/resources/{SOURCE_SYSTEM}/{asset_id}"


def _resource_actions(asset_id: int) -> list[UnifiedResourceAction]:
    return [
        UnifiedResourceAction(
            key="preview",
            label="播放视频",
            kind="preview",
            target="access_representation",
            url=f"/api/video/resources/{asset_id}/stream",
            enabled=True,
        ),
        UnifiedResourceAction(
            key="platform_detail",
            label="查看统一详情",
            kind="detail",
            target="platform",
            url=_resource_detail_url(asset_id),
        ),
        UnifiedResourceAction(
            key="source_detail",
            label="查看视频来源详情",
            kind="source_detail",
            target="source",
            url=f"/api/video/resources/{asset_id}",
        ),
        UnifiedResourceAction(
            key="download",
            label="下载视频文件",
            kind="download",
            target="source",
            url=f"/api/video/resources/{asset_id}/stream?download=1",
        ),
    ]


def _source_last_synced_at(db: Session) -> datetime:
    latest_created_at = db.query(func.max(VideoAsset.created_at)).scalar()
    if latest_created_at is None:
        return datetime.now(timezone.utc)
    return latest_created_at


def list_source_summary(db: Session) -> UnifiedResourceSourceSummary:
    resource_count = db.query(VideoAsset).count()
    return UnifiedResourceSourceSummary(
        source_system=SOURCE_SYSTEM,
        source_label=SOURCE_LABEL,
        resource_type=RESOURCE_TYPE,
        resource_count=resource_count,
        status="healthy",
        healthy=True,
        last_synced_at=_source_last_synced_at(db) if resource_count else None,
        entrypoint="/api/video/resources",
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
    normalized_profile_key = profile_key.strip() if profile_key else None
    if normalized_profile_key and normalized_profile_key not in PROFILE_DEFINITIONS:
        return []

    query = db.query(VideoAsset)

    if status:
        query = query.filter(VideoAsset.status == status)

    if resource_type:
        query = query.filter(VideoAsset.resource_type == resource_type)

    assets = query.order_by(VideoAsset.created_at.desc(), VideoAsset.id.desc()).all()

    resources: list[UnifiedResourceSummary] = []
    normalized_query = q.strip().lower() if q else None
    for asset in assets:
        layers = build_video_metadata_layers(
            asset_id=asset.id,
            asset_filename=asset.filename,
            asset_file_path=asset.file_path,
            asset_file_size=asset.file_size,
            asset_mime_type=asset.mime_type,
            asset_status=asset.status,
            asset_resource_type=asset.resource_type,
            asset_created_at=asset.created_at,
            asset_duration_seconds=asset.duration_seconds,
            asset_width=asset.width,
            asset_height=asset.height,
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
            search_tokens.extend(str(value) for value in (layers.get("raw_metadata") or {}).values())
            search_blob = " ".join(search_tokens).lower()
            if normalized_query not in search_blob:
                continue

        # Video is always preview-enabled if status is ready
        video_preview_enabled = asset.status == "ready"
        if preview_enabled is not None and preview_enabled != video_preview_enabled:
            continue

        resources.append(
            UnifiedResourceSummary(
                id=_platform_id(asset.id),
                source_system=SOURCE_SYSTEM,
                source_id=str(asset.id),
                source_label=SOURCE_LABEL,
                title=str(layers["core"].get("title") or asset.filename),
                resource_type=asset.resource_type or RESOURCE_TYPE,
                profile_key=asset_profile_key,
                profile_label=str((layers.get("core") or {}).get("profile_label") or PROFILE_DEFINITIONS[asset_profile_key]["label"]),
                status=asset.status,
                preview_enabled=video_preview_enabled,
                manifest_url=f"/api/video/resources/{asset.id}/stream",
                thumbnail_url=f"/api/video/resources/{asset.id}/stream",
                detail_url=_resource_detail_url(asset.id),
                updated_at=asset.created_at,
                actions=_resource_actions(asset.id),
            )
        )
    return resources


def _build_video_rights_display(layers: dict[str, object], metadata_info: dict[str, object] | None) -> dict[str, object] | None:
    """Build minimal rights_display for video from metadata layers or metadata_info."""
    rights = layers.get("rights") if isinstance(layers, dict) else {}
    if isinstance(rights, dict):
        owner = rights.get("copyright_owner") or ""
        status = rights.get("copyright_status") or ""
        license_val = rights.get("license") or ""
        if owner or status or license_val:
            statement = f"© {owner}" if owner else ""
            return {
                "statement": statement,
                "credit_line": owner,
                "copyright_status": status or None,
                "license": license_val or None,
            }
    # Fallback: check metadata_info for rights_label
    if metadata_info:
        label = metadata_info.get("rights_label") or metadata_info.get("license_label") or ""
        if label:
            return {"statement": label, "credit_line": ""}
    return None


def get_unified_resource(asset_id: int, db: Session) -> UnifiedResourceDetail:
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if asset is None:
        raise LookupError("Resource not found")

    layers = build_video_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_created_at=asset.created_at,
        asset_duration_seconds=asset.duration_seconds,
        asset_width=asset.width,
        asset_height=asset.height,
        metadata=asset.metadata_info or {},
    )

    return UnifiedResourceDetail(
        id=_platform_id(asset.id),
        source_system=SOURCE_SYSTEM,
        source_id=str(asset.id),
        source_label=SOURCE_LABEL,
        title=str(layers["core"].get("title") or asset.filename),
        resource_type=asset.resource_type or RESOURCE_TYPE,
        profile_key=str((layers.get("core") or {}).get("profile_key") or "other"),
        profile_label=str((layers.get("core") or {}).get("profile_label") or PROFILE_DEFINITIONS[str((layers.get("core") or {}).get("profile_key") or "other")]["label"]),
        status=asset.status,
        preview_enabled=asset.status == "ready",
        manifest_url=f"/api/video/resources/{asset.id}/stream",
        thumbnail_url=f"/api/video/resources/{asset.id}/stream",
        detail_url=_resource_detail_url(asset.id),
        updated_at=asset.created_at,
        actions=_resource_actions(asset.id),
        source_detail_url=f"/api/video/resources/{asset.id}",
        source_record_type="video_asset",
        source_record_schema="video_asset.v1",
        source_record={
            "id": asset.id,
            "filename": asset.filename,
            "file_path": asset.file_path,
            "file_size": asset.file_size,
            "mime_type": asset.mime_type,
            "duration_seconds": asset.duration_seconds,
            "width": asset.width,
            "height": asset.height,
            "status": asset.status,
            "resource_type": asset.resource_type,
            "created_at": asset.created_at.isoformat() if asset.created_at else None,
            "title": layers["core"].get("title"),
            "structure": {
                "summary": f"视频文件 · {asset.mime_type or 'video/mp4'} · {asset.file_size} bytes",
                "primary_file": {
                    "filename": asset.filename,
                    "file_path": asset.file_path,
                    "file_size": asset.file_size,
                    "mime_type": asset.mime_type,
                },
            },
        },
        rights_display=_build_video_rights_display(layers, asset.metadata_info or {}),
    )


class VideoSourceAdapter(PlatformSourceAdapter):
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

    def get_unified_resource_by_source(
        self,
        source_system: str,
        source_id: str,
        db: Session,
    ) -> UnifiedResourceDetail:
        if source_system != SOURCE_SYSTEM or not source_id.isdigit():
            raise ValueError("Unknown unified resource id")
        return get_unified_resource(int(source_id), db)


registry.register(VideoSourceAdapter())
