from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping

METADATA_SCHEMA_VERSION = "1.1"
SOURCE_SYSTEM = "video"
SOURCE_LABEL = "视频子系统"

PROFILE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "mission_documentary": {"key": "mission_documentary", "label": "航天任务纪实", "sheet": "航天任务纪实"},
    "science_education": {"key": "science_education", "label": "科普教育", "sheet": "科普教育"},
    "human_spaceflight": {"key": "human_spaceflight", "label": "载人航天", "sheet": "载人航天"},
    "other": {"key": "other", "label": "其他", "sheet": "其他"},
}

RESOURCE_TYPE_LABELS: dict[str, str] = {
    "video_cultural_object": "文博视频",
}


def _as_dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _lookup(meta: Mapping[str, Any], key: str, default: Any = None) -> Any:
    value = meta.get(key)
    if value not in (None, ""):
        return value
    for section_name in ("core", "management", "technical", "rights"):
        section = meta.get(section_name)
        if isinstance(section, Mapping) and section.get(key) not in (None, ""):
            return section[key]
    profile = meta.get("profile")
    if isinstance(profile, Mapping):
        fields = profile.get("fields")
        if isinstance(fields, Mapping) and fields.get(key) not in (None, ""):
            return fields[key]
    raw = meta.get("raw_metadata")
    if isinstance(raw, Mapping):
        if raw.get(key) not in (None, ""):
            return raw[key]
        business = raw.get("business_metadata")
        if isinstance(business, Mapping) and business.get(key) not in (None, ""):
            return business[key]
    return default


def _first_present(*values: Any) -> Any:
    return next((value for value in values if value not in (None, "")), None)


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
    source_metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    meta = dict(metadata or {})
    existing_core = _as_dict(meta.get("core"))
    existing_management = _as_dict(meta.get("management"))
    existing_technical = _as_dict(meta.get("technical"))
    existing_rights = _as_dict(meta.get("rights"))
    existing_profile = _as_dict(meta.get("profile"))
    existing_raw = _as_dict(meta.get("raw_metadata"))

    resource_type = asset_resource_type or str(_lookup(meta, "resource_type", "video_cultural_object"))
    title = str(_lookup(meta, "title", asset_filename or "Untitled Video"))
    profile_key = str(_lookup(meta, "profile_key", existing_profile.get("key") or "other"))
    if profile_key not in PROFILE_DEFINITIONS:
        profile_key = "other"
    profile_definition = PROFILE_DEFINITIONS[profile_key]

    core: dict[str, Any] = {
        "title": title,
        "resource_type": resource_type,
        "resource_type_label": RESOURCE_TYPE_LABELS.get(resource_type, resource_type),
        "source_system": SOURCE_SYSTEM,
        "source_label": SOURCE_LABEL,
        "source_id": str(asset_id) if asset_id is not None else _lookup(meta, "source_id"),
        "status": asset_status or _lookup(meta, "status", "processing"),
        "preview_enabled": (asset_status or _lookup(meta, "status")) == "ready",
        "profile_key": profile_key,
        "profile_label": profile_definition["label"],
        "profile_sheet": profile_definition["sheet"],
    }
    core.update({key: value for key, value in existing_core.items() if value not in (None, "")})
    if asset_id is not None:
        core["source_id"] = str(asset_id)
    if asset_status:
        core["status"] = asset_status
        core["preview_enabled"] = asset_status == "ready"

    technical: dict[str, Any] = {
        "filename": asset_filename or _lookup(meta, "filename"),
        "file_path": asset_file_path or _lookup(meta, "file_path"),
        "file_size": _first_present(asset_file_size, _lookup(meta, "file_size")),
        "mime_type": asset_mime_type or _lookup(meta, "mime_type", "video/mp4"),
        "format_name": _lookup(meta, "format_name", "MP4"),
        "format_version": _lookup(meta, "format_version", "ISO Base Media"),
        "duration_seconds": _first_present(asset_duration_seconds, _lookup(meta, "duration_seconds")),
        "duration_seconds_exact": _lookup(meta, "duration_seconds_exact"),
        "width": _first_present(asset_width, _lookup(meta, "width")),
        "height": _first_present(asset_height, _lookup(meta, "height")),
        "frame_rate": _lookup(meta, "frame_rate"),
        "frame_count": _lookup(meta, "frame_count"),
        "codec": _lookup(meta, "codec"),
        "aspect_ratio": _lookup(meta, "aspect_ratio"),
        "checksum_algorithm": _lookup(meta, "checksum_algorithm", "SHA256"),
        "checksum": _lookup(meta, "checksum"),
        "poster_filename": _lookup(meta, "poster_filename"),
        "poster_file_path": _lookup(meta, "poster_file_path"),
        "poster_mime_type": _lookup(meta, "poster_mime_type", "image/jpeg"),
        "source_variant": _lookup(meta, "source_variant"),
        "source_download_url": _lookup(meta, "source_download_url"),
    }
    technical.update({key: value for key, value in existing_technical.items() if value not in (None, "")})
    if asset_filename:
        technical["filename"] = asset_filename
    if asset_file_path:
        technical["file_path"] = asset_file_path
    if asset_file_size is not None:
        technical["file_size"] = asset_file_size
    if asset_duration_seconds is not None:
        technical["duration_seconds"] = asset_duration_seconds
    if asset_width is not None:
        technical["width"] = asset_width
    if asset_height is not None:
        technical["height"] = asset_height

    management: dict[str, Any] = {
        "status": asset_status or _lookup(meta, "status"),
        "created_at": asset_created_at.isoformat() if asset_created_at else _lookup(meta, "created_at"),
        "project_name": _lookup(meta, "project_name"),
        "producer": _lookup(meta, "producer"),
        "producer_org": _lookup(meta, "producer_org"),
        "source_center": _lookup(meta, "source_center"),
        "date_created": _lookup(meta, "date_created"),
        "description": _lookup(meta, "description"),
        "keywords": _lookup(meta, "keywords"),
        "language": _lookup(meta, "language", "en"),
        "ingest_method": _lookup(meta, "ingest_method"),
        "record_time": _lookup(meta, "record_time"),
        "source_url": _lookup(meta, "source_url"),
    }
    management.update({key: value for key, value in existing_management.items() if value not in (None, "")})

    rights: dict[str, Any] = {
        "copyright_status": _lookup(meta, "copyright_status"),
        "copyright_owner": _lookup(meta, "copyright_owner"),
        "access_scope": _lookup(meta, "access_scope", "公开"),
        "allowed_usage": _lookup(meta, "allowed_usage"),
        "license": _lookup(meta, "license"),
        "license_url": _lookup(meta, "license_url"),
        "allow_derivatives": _lookup(meta, "allow_derivatives"),
        "usage_restrictions": _lookup(meta, "usage_restrictions"),
        "rights_holder": _lookup(meta, "rights_holder"),
        "permission_notes": _lookup(meta, "permission_notes"),
    }
    rights.update({key: value for key, value in existing_rights.items() if value not in (None, "")})

    profile_fields = {
        "category": _lookup(meta, "category", profile_definition["label"]),
        "mission": _lookup(meta, "mission"),
        "program": _lookup(meta, "program"),
        "topic": _lookup(meta, "topic"),
        "audience": _lookup(meta, "audience"),
    }
    existing_fields = _as_dict(existing_profile.get("fields"))
    profile_fields.update({key: value for key, value in existing_fields.items() if value not in (None, "")})
    profile = {**profile_definition, "fields": profile_fields}

    copyright_owner = rights.get("copyright_owner") or rights.get("rights_holder") or ""
    rights_display = {
        "statement": str(rights.get("copyright_status") or (f"© {copyright_owner}" if copyright_owner else "")),
        "credit_line": copyright_owner,
        "license": rights.get("license"),
        "license_url": rights.get("license_url"),
        "copyright_status": rights.get("copyright_status"),
        "usage_restrictions": rights.get("usage_restrictions"),
        "allow_derivatives": rights.get("allow_derivatives"),
    }

    raw_metadata = deepcopy(source_metadata if source_metadata is not None else existing_raw or meta)
    return {
        "schema_version": METADATA_SCHEMA_VERSION,
        "core": core,
        "management": management,
        "technical": technical,
        "profile": profile,
        "rights": rights,
        "rights_display": rights_display,
        "raw_metadata": raw_metadata,
    }
