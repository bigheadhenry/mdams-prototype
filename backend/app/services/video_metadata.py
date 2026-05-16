from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

METADATA_SCHEMA_VERSION = "1.0"
SOURCE_SYSTEM = "video"
SOURCE_LABEL = "视频子系统"

PROFILE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "other": {"key": "other", "label": "其他", "sheet": "其他"},
}

RESOURCE_TYPE_LABELS: dict[str, str] = {
    "video_cultural_object": "文博视频",
}


def _safe_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def build_video_metadata_layers(
    *,
    asset_id: int | None,
    asset_filename: str | None,
    asset_file_path: str | None,
    asset_file_size: int | None,
    asset_mime_type: str | None,
    asset_status: str | None,
    asset_resource_type: str | None,
    asset_created_at: datetime | None,
    asset_duration_seconds: int | None = None,
    asset_width: int | None = None,
    asset_height: int | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    meta = dict(metadata or {})

    resource_type = asset_resource_type or "video_cultural_object"
    title = _safe_str(meta.get("title")) or asset_filename or "Untitled Video"

    core: dict[str, Any] = {
        "title": title,
        "resource_type": resource_type,
        "resource_type_label": RESOURCE_TYPE_LABELS.get(resource_type, resource_type),
        "source_system": SOURCE_SYSTEM,
        "source_label": SOURCE_LABEL,
        "source_id": str(asset_id) if asset_id else None,
        "profile_key": "other",
        "profile_label": "其他",
    }

    technical: dict[str, Any] = {
        "filename": asset_filename,
        "file_path": asset_file_path,
        "file_size": asset_file_size,
        "mime_type": asset_mime_type,
        "duration_seconds": asset_duration_seconds,
        "width": asset_width,
        "height": asset_height,
    }

    management: dict[str, Any] = {
        "status": asset_status,
        "created_at": asset_created_at.isoformat() if asset_created_at else None,
    }

    return {
        "schema_version": METADATA_SCHEMA_VERSION,
        "core": core,
        "management": management,
        "technical": technical,
        "profile": PROFILE_DEFINITIONS.get("other"),
        "raw_metadata": meta,
    }
