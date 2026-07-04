"""Metadata standards mapping — Dublin Core 15 output.

Implements lossless conversion from MDAMS internal resource data
to Dublin Core 15-element metadata set.

Usage:
    from .metadata_standards import to_dublin_core
    dc_json = to_dublin_core(resource_data)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def to_dublin_core(
    *,
    title: str | None = None,
    creator: str | None = None,       # photographer
    subject: str | None = None,       # combined profile fields
    description: str | None = None,   # shooting_content
    publisher: str | None = "故宫博物院",
    contributor: str | None = None,
    date: str | None = None,          # shooting_date or updated_at
    type_: str | None = None,         # resource_type
    format_: str | None = None,       # format / mime / resolution
    identifier: str | None = None,    # source_system:source_id
    language: str | None = "zh-CN",
    rights: str | None = None,        # copyright_status + usage_restrictions
    # Unmapped (always omitted):
    # source, relation, coverage
    **extra: Any,
) -> dict[str, Any]:
    """Build a Dublin Core 15-element dictionary.

    Returns only populated elements — null/empty values are omitted.
    The 3 unmapped elements (source, relation, coverage) are never output.
    """
    dc: dict[str, Any] = {}

    _set(dc, "dc:title", title)
    _set(dc, "dc:creator", creator)
    _set(dc, "dc:subject", subject)
    _set(dc, "dc:description", description)
    _set(dc, "dc:publisher", publisher)
    _set(dc, "dc:contributor", contributor)
    _set(dc, "dc:date", date)
    _set(dc, "dc:type", type_)
    _set(dc, "dc:format", format_)
    _set(dc, "dc:identifier", identifier)
    _set(dc, "dc:language", language)
    _set(dc, "dc:rights", rights)
    # source / relation / coverage: intentionally omitted per user decision

    return dc


def to_dublin_core_json(
    *,
    title: str | None = None,
    creator: str | None = None,
    subject: str | None = None,
    description: str | None = None,
    publisher: str | None = "故宫博物院",
    contributor: str | None = None,
    date: str | None = None,
    type_: str | None = None,
    format_: str | None = None,
    identifier: str | None = None,
    language: str | None = "zh-CN",
    rights: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Return a Dublin Core record as a namespaced JSON dict.

    All DC elements are wrapped in a top-level ``dublin_core`` key
    for clean API integration.
    """
    dc = to_dublin_core(
        title=title,
        creator=creator,
        subject=subject,
        description=description,
        publisher=publisher,
        contributor=contributor,
        date=date,
        type_=type_,
        format_=format_,
        identifier=identifier,
        language=language,
        rights=rights,
    )
    return {"dublin_core": dc}


# ── Helper ───────────────────────────────────────────────────────────

def _set(d: dict[str, Any], key: str, value: Any) -> None:
    """Set *key* in *d* only if *value* is not None and not empty."""
    if value is not None and value != "":
        d[key] = value


# ── Resource adapter ─────────────────────────────────────────────────

def from_unified_resource_detail(detail: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a Dublin Core record from a UnifiedResourceDetail object.

    This is the primary integration point — call it from the platform
    router when ``format=dc`` is requested.
    """
    cfg = config or {}

    # Extract core fields
    title = _get(detail, "title")
    source_system = _get(detail, "source_system")
    source_id = _get(detail, "source_id")
    resource_type = _get(detail, "resource_type")
    format_val = _get(detail, "format")
    updated_at = _get(detail, "updated_at")
    identifier = f"{source_system}:{source_id}" if source_system and source_id else None

    # Extract profile / management metadata from source_record
    record = _get(detail, "source_record")
    profile = {}
    management = {}
    if isinstance(record, dict):
        profile = record.get("profile") or record.get("metadata") or {}
        management = record.get("management") or {}

    # Map fields
    creator = (
        _get(management, "photographer")
        or _get(profile, "photographer")
        or cfg.get("default_creator")
    )
    description = _get(management, "shooting_content") or _get(profile, "shooting_content")
    subject_parts = [
        _get(profile, "object_name"),
        _get(profile, "era"),
        description,
    ]
    subject = " · ".join(p for p in subject_parts if p) or None
    date = (
        _get(management, "shooting_date")
        or _get(profile, "shooting_date")
        or _format_date(updated_at)
    )
    format_str = " / ".join(
        p for p in [format_val, _get(detail, "mime_type"), _get(detail, "resolution")]
        if p
    ) or None

    # Rights
    rights_parts = [
        _get_profile_field(record, "copyright_status"),
        _get_profile_field(record, "usage_restrictions"),
    ]
    rights = "；".join(p for p in rights_parts if p) or _get_profile_field(record, "copyright_owner")

    return to_dublin_core_json(
        title=title,
        creator=creator,
        subject=subject,
        description=description,
        publisher=cfg.get("publisher", "故宫博物院"),
        contributor=_get_profile_field(record, "contributor"),
        date=date,
        type_=resource_type,
        format_=format_str,
        identifier=identifier,
        language=cfg.get("language", "zh-CN"),
        rights=rights,
    )


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Safely get an attribute or dict key."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _get_profile_field(record: dict[str, Any] | None, field: str) -> str | None:
    """Get a field from the source_record's rights or profile metadata."""
    if not isinstance(record, dict):
        return None
    rights = record.get("rights") or {}
    val = rights.get(field)
    if val:
        return str(val)
    profile = record.get("profile") or record.get("metadata") or {}
    return str(profile.get(field)) if profile.get(field) else None


def _format_date(dt: Any) -> str | None:
    """Format a datetime value as ISO-8601 date string."""
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    if isinstance(dt, str):
        return dt
    return str(dt)
