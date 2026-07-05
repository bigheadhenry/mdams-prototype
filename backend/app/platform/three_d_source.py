from __future__ import annotations

from datetime import datetime, timezone
from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import ThreeDAsset
from ..schemas import (
    UnifiedResourceAction,
    UnifiedResourceDetail,
    UnifiedResourceSourceSummary,
    UnifiedResourceSummary,
)
from ..services.three_d_detail import build_three_d_detail_response
from ..services.three_d_metadata import PROFILE_DEFINITIONS, SOURCE_LABEL, SOURCE_SYSTEM, build_three_d_metadata_layers
from .base import PlatformSourceAdapter
from .registry import registry

RESOURCE_TYPE = "three_d_digital_object"


def _platform_id(asset_id: int) -> str:
    return f"{SOURCE_SYSTEM}:{asset_id}"


def _object_source_id(anchor_asset_id: int) -> str:
    return f"object-{anchor_asset_id}"


def _object_platform_id(anchor_asset_id: int) -> str:
    return f"{SOURCE_SYSTEM}:{_object_source_id(anchor_asset_id)}"


def _object_actions(
    source_id: str,
    *,
    preview_asset_id: int | None,
    preview_enabled: bool,
) -> list[UnifiedResourceAction]:
    preview_url = f"/api/three-d/resources/{preview_asset_id}" if preview_asset_id is not None else None
    return [
        UnifiedResourceAction(
            key="preview",
            label="打开三维预览",
            kind="preview",
            target="access_representation",
            url=preview_url,
            enabled=preview_enabled and preview_url is not None,
            reason=None if preview_enabled else "This 3D object has no representation ready for web preview.",
        ),
        UnifiedResourceAction(
            key="platform_detail",
            label="查看统一详情",
            kind="detail",
            target="platform",
            url=f"/api/platform/resources/{SOURCE_SYSTEM}/{source_id}",
        ),
        UnifiedResourceAction(
            key="source_detail",
            label="查看三维对象来源详情",
            kind="source_detail",
            target="source",
            url=f"/api/platform/resources/{SOURCE_SYSTEM}/{source_id}",
        ),
        UnifiedResourceAction(
            key="download",
            label="下载默认展示资源包",
            kind="download",
            target="source",
            url=f"/api/three-d/resources/{preview_asset_id}/download" if preview_asset_id is not None else None,
            enabled=preview_asset_id is not None,
        ),
    ]


def _resource_actions(asset_id: int, *, preview_enabled: bool) -> list[UnifiedResourceAction]:
    return [
        UnifiedResourceAction(
            key="preview",
            label="打开三维预览",
            kind="preview",
            target="access_representation",
            url=f"/api/three-d/resources/{asset_id}",
            enabled=preview_enabled,
            reason=None if preview_enabled else "This 3D version is not marked ready for web preview.",
        ),
        UnifiedResourceAction(
            key="platform_detail",
            label="查看统一详情",
            kind="detail",
            target="platform",
            url=f"/api/platform/resources/{SOURCE_SYSTEM}/{asset_id}",
        ),
        UnifiedResourceAction(
            key="source_detail",
            label="查看三维来源详情",
            kind="source_detail",
            target="source",
            url=f"/api/three-d/resources/{asset_id}",
        ),
        UnifiedResourceAction(
            key="download",
            label="下载三维资源包",
            kind="download",
            target="source",
            url=f"/api/three-d/resources/{asset_id}/download",
        ),
    ]


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


def _object_key(asset: ThreeDAsset) -> tuple[int | None, str]:
    group = (asset.resource_group or "").strip() or f"asset-{asset.id}"
    return asset.collection_object_id, group


def _representation_type(asset: ThreeDAsset, layers: dict[str, object]) -> str:
    for section_key in ("core", "management", "profile", "raw_metadata"):
        section = layers.get(section_key)
        if isinstance(section, dict):
            value = section.get("representation_type")
            if value:
                return str(value)
            fields = section.get("fields")
            if isinstance(fields, dict) and fields.get("representation_type"):
                return str(fields["representation_type"])

    version = (asset.version_label or "").lower()
    if "original" in version or "master" in version:
        return "original_master"
    if "mobile" in version or "light" in version:
        return "mobile_lightweight"
    if "detail" in version or "research" in version or "high" in version:
        return "research_detail"
    if "web" in version or bool(asset.is_web_preview and asset.web_preview_status == "ready"):
        return "web_display"
    return "derivative"


REPRESENTATION_TYPE_LABELS = {
    "original_master": "原始保存级",
    "web_display": "Web 展示级",
    "mobile_lightweight": "移动轻量级",
    "research_detail": "高精度研究级",
    "derivative": "其他派生",
}


def _representation_label(representation_type: str) -> str:
    return REPRESENTATION_TYPE_LABELS.get(representation_type, representation_type)


def _asset_layers(asset: ThreeDAsset) -> dict[str, object]:
    return build_three_d_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_created_at=asset.created_at,
        metadata=asset.metadata_info or {},
        file_records=_asset_file_records(asset),
    )


def _choose_default_preview_asset(assets: list[ThreeDAsset]) -> ThreeDAsset | None:
    previewable = [
        asset
        for asset in assets
        if asset.is_web_preview and asset.web_preview_status == "ready" and asset.status == "ready"
    ]
    if not previewable:
        return None

    def sort_key(asset: ThreeDAsset) -> tuple[int, int, datetime]:
        layers = _asset_layers(asset)
        representation_type = _representation_type(asset, layers)
        priority = 0 if representation_type == "web_display" else 1
        current_rank = 0 if asset.is_current else 1
        return priority, current_rank, asset.created_at

    return sorted(previewable, key=sort_key)[0]


def _object_title(assets: list[ThreeDAsset], layers_by_id: dict[int, dict[str, object]]) -> str:
    first_asset = assets[0]
    collection_object = first_asset.collection_object
    if collection_object and collection_object.object_name:
        object_name = collection_object.object_name
        return object_name if "三维数字对象" in object_name else f"{object_name}三维数字对象"
    group = first_asset.resource_group or ""
    if group:
        return group
    layers = layers_by_id.get(first_asset.id) or {}
    return str((layers.get("core") or {}).get("title") or first_asset.filename)


def _object_search_blob(assets: list[ThreeDAsset], layers_by_id: dict[int, dict[str, object]]) -> str:
    tokens: list[str] = []
    for asset in assets:
        layers = layers_by_id[asset.id]
        tokens.extend(
            [
                str(asset.id),
                asset.filename or "",
                asset.file_path or "",
                asset.mime_type or "",
                asset.resource_group or "",
                asset.version_label or "",
                asset.web_preview_status or "",
            ]
        )
        if asset.collection_object:
            tokens.extend(
                str(value or "")
                for value in (
                    asset.collection_object.object_number,
                    asset.collection_object.object_name,
                    asset.collection_object.object_type,
                    asset.collection_object.collection_unit,
                    asset.collection_object.summary,
                    asset.collection_object.keywords,
                )
            )
        for section_key in ("core", "management", "collection", "technical", "preservation", "raw_metadata"):
            section = layers.get(section_key)
            if isinstance(section, dict):
                tokens.extend(str(value) for value in section.values())
        profile = layers.get("profile")
        if isinstance(profile, dict):
            tokens.extend(str(value) for value in profile.values() if not isinstance(value, dict))
            fields = profile.get("fields")
            if isinstance(fields, dict):
                tokens.extend(str(value) for value in fields.values())
    return " ".join(tokens).lower()


def _representation_summary(asset: ThreeDAsset, layers: dict[str, object]) -> dict[str, object]:
    detail = build_three_d_detail_response(asset)
    representation_type = _representation_type(asset, layers)
    return {
        "id": asset.id,
        "source_id": str(asset.id),
        "title": detail.title,
        "representation_type": representation_type,
        "representation_label": _representation_label(representation_type),
        "version_label": asset.version_label or "v1",
        "version_order": asset.version_order or 0,
        "is_current": bool(asset.is_current),
        "is_web_preview": bool(asset.is_web_preview),
        "web_preview_status": asset.web_preview_status or "disabled",
        "preview_enabled": bool(detail.viewer and detail.viewer.enabled),
        "file_count": len(detail.structure.files),
        "file_groups": [group.model_dump(mode="json") for group in detail.structure.groups],
        "download_url": detail.outputs.download_url,
        "detail_url": f"/api/three-d/resources/{asset.id}",
        "viewer": detail.viewer.model_dump(mode="json") if detail.viewer else None,
        "preview_data": _preview_data_from_layers(layers),
        "preservation": detail.preservation.model_dump(mode="json"),
    }


def _preview_data_from_layers(layers: dict[str, object]) -> dict[str, object] | None:
    raw = layers.get("raw_metadata")
    if isinstance(raw, dict) and isinstance(raw.get("preview_data"), dict):
        return raw["preview_data"]
    technical = layers.get("technical")
    if isinstance(technical, dict) and isinstance(technical.get("preview_data"), dict):
        return technical["preview_data"]
    return None


def _build_rights_display_from_layers(layers: dict[str, object]) -> dict[str, object] | None:
    """Build minimal rights_display from 3D metadata layers."""
    rights = layers.get("rights") if isinstance(layers, dict) else {}
    if not isinstance(rights, dict):
        return None
    copyright_owner = rights.get("copyright_owner") or ""
    copyright_status = rights.get("copyright_status") or ""
    license_val = rights.get("license") or ""
    if not (copyright_owner or copyright_status or license_val):
        return None
    statement = f"© {copyright_owner}" if copyright_owner else ""
    return {
        "statement": statement,
        "credit_line": copyright_owner,
        "copyright_status": copyright_status or None,
        "license": license_val or None,
    }


def list_source_summary(db: Session) -> UnifiedResourceSourceSummary:
    assets = db.query(ThreeDAsset).all()
    resource_count = len({_object_key(asset) for asset in assets})
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
    if resource_type and resource_type != RESOURCE_TYPE:
        query = query.filter(ThreeDAsset.resource_type == resource_type)

    assets = query.order_by(ThreeDAsset.created_at.desc(), ThreeDAsset.id.desc()).all()
    resources: list[UnifiedResourceSummary] = []
    normalized_query = q.strip().lower() if q else None
    normalized_profile_key = profile_key.strip() if profile_key else None
    if normalized_profile_key and normalized_profile_key not in PROFILE_DEFINITIONS:
        return []

    grouped_assets: dict[tuple[int | None, str], list[ThreeDAsset]] = defaultdict(list)
    layers_by_id: dict[int, dict[str, object]] = {}
    for asset in assets:
        grouped_assets[_object_key(asset)].append(asset)
        layers_by_id[asset.id] = _asset_layers(asset)

    for _key, object_assets in grouped_assets.items():
        object_assets = sorted(object_assets, key=lambda item: (item.version_order or 0, item.created_at, item.id))
        profile_keys = {
            str((layers_by_id[asset.id].get("core") or {}).get("profile_key") or "other")
            for asset in object_assets
        }
        if normalized_profile_key and normalized_profile_key not in profile_keys:
            continue

        if normalized_query and normalized_query not in _object_search_blob(object_assets, layers_by_id):
            continue

        default_preview_asset = _choose_default_preview_asset(object_assets)
        default_preview_layers = layers_by_id.get(default_preview_asset.id) if default_preview_asset else None
        object_preview_data = _preview_data_from_layers(default_preview_layers or {}) if default_preview_layers else None
        object_preview_enabled = default_preview_asset is not None
        if preview_enabled is not None and preview_enabled != object_preview_enabled:
            continue

        anchor_asset = object_assets[0]
        source_id = _object_source_id(anchor_asset.id)
        total_file_count = sum(len(asset.files or []) for asset in object_assets)
        object_status = "ready" if any(asset.status == "ready" for asset in object_assets) else object_assets[0].status
        updated_at = max(asset.created_at for asset in object_assets)
        resources.append(
            UnifiedResourceSummary(
                id=_object_platform_id(anchor_asset.id),
                source_system=SOURCE_SYSTEM,
                source_id=source_id,
                source_label=SOURCE_LABEL,
                title=_object_title(object_assets, layers_by_id),
                resource_type=RESOURCE_TYPE,
                profile_key="three_d_object",
                profile_label=f"三维数字对象 · {len(object_assets)} 个表现 · {total_file_count} 个文件",
                status=object_status,
                preview_enabled=object_preview_enabled,
                manifest_url=f"/api/three-d/resources/{default_preview_asset.id}" if default_preview_asset else f"/api/platform/resources/{SOURCE_SYSTEM}/{source_id}",
                thumbnail_url=str(object_preview_data.get("poster_url")) if object_preview_data and object_preview_data.get("poster_url") else None,
                preview_data=object_preview_data,
                detail_url=f"/api/platform/resources/{SOURCE_SYSTEM}/{source_id}",
                updated_at=updated_at,
                actions=_object_actions(
                    source_id,
                    preview_asset_id=default_preview_asset.id if default_preview_asset else None,
                    preview_enabled=object_preview_enabled,
                ),
            )
        )
    return resources


def _assets_for_object(anchor_asset: ThreeDAsset, db: Session) -> list[ThreeDAsset]:
    collection_object_id, group = _object_key(anchor_asset)
    query = db.query(ThreeDAsset).filter(ThreeDAsset.resource_group == group)
    if collection_object_id is None:
        query = query.filter(ThreeDAsset.collection_object_id.is_(None))
    else:
        query = query.filter(ThreeDAsset.collection_object_id == collection_object_id)
    return query.order_by(ThreeDAsset.version_order.asc(), ThreeDAsset.created_at.asc(), ThreeDAsset.id.asc()).all()


def get_unified_resource(asset_id: int, db: Session) -> UnifiedResourceDetail:
    asset = db.query(ThreeDAsset).filter(ThreeDAsset.id == asset_id).first()
    if asset is None:
        raise LookupError("Resource not found")

    object_assets = _assets_for_object(asset, db)
    layers_by_id = {item.id: _asset_layers(item) for item in object_assets}
    default_preview_asset = _choose_default_preview_asset(object_assets)
    default_preview_layers = layers_by_id.get(default_preview_asset.id) if default_preview_asset else None
    object_preview_data = _preview_data_from_layers(default_preview_layers or {}) if default_preview_layers else None
    default_detail = build_three_d_detail_response(default_preview_asset or object_assets[0])
    anchor_asset = object_assets[0]
    source_id = _object_source_id(anchor_asset.id)
    total_file_count = sum(len(item.files or []) for item in object_assets)
    representations = [_representation_summary(item, layers_by_id[item.id]) for item in object_assets]
    collection_object = anchor_asset.collection_object
    object_title = _object_title(object_assets, layers_by_id)
    object_status = "ready" if any(item.status == "ready" for item in object_assets) else anchor_asset.status
    updated_at = max(item.created_at for item in object_assets)
    preview_enabled = default_preview_asset is not None
    source_record = {
        "id": source_id,
        "title": object_title,
        "resource_type": RESOURCE_TYPE,
        "source_record_schema": "three_d_object_detail.v1",
        "collection_object": {
            "id": collection_object.id,
            "object_number": collection_object.object_number,
            "object_name": collection_object.object_name,
            "object_type": collection_object.object_type,
            "collection_unit": collection_object.collection_unit,
            "summary": collection_object.summary,
            "keywords": collection_object.keywords,
        } if collection_object else None,
        "structure": {
            "summary": f"{len(object_assets)} 个模型表现，{total_file_count} 个文件。默认预览：{default_detail.version_label if default_preview_asset else '无'}。",
            "representation_count": len(object_assets),
            "file_count": total_file_count,
        },
        "default_preview_representation_id": default_preview_asset.id if default_preview_asset else None,
        "default_preview": default_detail.model_dump(mode="json") if default_preview_asset else None,
        "preview_data": object_preview_data,
        "representations": representations,
    }

    return UnifiedResourceDetail(
        id=_object_platform_id(anchor_asset.id),
        source_system=SOURCE_SYSTEM,
        source_id=source_id,
        source_label=SOURCE_LABEL,
        title=object_title,
        resource_type=RESOURCE_TYPE,
        profile_key="three_d_object",
        profile_label=f"三维数字对象 · {len(object_assets)} 个表现 · {total_file_count} 个文件",
        status=object_status,
        preview_enabled=preview_enabled,
        manifest_url=f"/api/three-d/resources/{default_preview_asset.id}" if default_preview_asset else f"/api/platform/resources/{SOURCE_SYSTEM}/{source_id}",
        thumbnail_url=str(object_preview_data.get("poster_url")) if object_preview_data and object_preview_data.get("poster_url") else None,
        preview_data=object_preview_data,
        detail_url=f"/api/platform/resources/{SOURCE_SYSTEM}/{source_id}",
        updated_at=updated_at,
        actions=_object_actions(
            source_id,
            preview_asset_id=default_preview_asset.id if default_preview_asset else None,
            preview_enabled=preview_enabled,
        ),
        source_detail_url=f"/api/platform/resources/{SOURCE_SYSTEM}/{source_id}",
        source_record_type="three_d_object_detail",
        source_record_schema="three_d_object_detail.v1",
        source_record=source_record,
        rights_display=_build_rights_display_from_layers(default_preview_layers or layers_by_id.get(anchor_asset.id, {})),
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

    def get_unified_resource_by_source(
        self,
        source_system: str,
        source_id: str,
        db: Session,
    ) -> UnifiedResourceDetail:
        if source_system != SOURCE_SYSTEM:
            raise ValueError("Unknown unified resource id")
        if source_id.startswith("object-") and source_id.removeprefix("object-").isdigit():
            return get_unified_resource(int(source_id.removeprefix("object-")), db)
        if source_id.isdigit():
            return get_unified_resource(int(source_id), db)
        raise ValueError("Unknown unified resource id")


registry.register(ThreeDSourceAdapter())
