from __future__ import annotations

from typing import Any, Mapping

from sqlalchemy.orm import Session

from ..models import ThreeDCollectionObject, ThreeDDigitalObject
from .three_d_workflow import PUBLICATION_STATUSES, REPRESENTATION_TYPES


def _optional_text(value: object | None) -> str | None:
    return value.strip() or None if isinstance(value, str) else None


def infer_representation_type(
    *,
    explicit: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    version_label: str | None = None,
    is_web_preview: bool = False,
    web_preview_status: str | None = None,
) -> str:
    candidate = explicit.strip().lower() if isinstance(explicit, str) else ""
    if candidate in REPRESENTATION_TYPES:
        return candidate

    source = metadata if isinstance(metadata, Mapping) else {}
    for section_name in ("core", "management", "profile", "raw_metadata"):
        section = source.get(section_name)
        if not isinstance(section, Mapping):
            continue
        value = section.get("representation_type")
        if not value and isinstance(section.get("fields"), Mapping):
            value = section["fields"].get("representation_type")
        normalized = str(value or "").strip().lower()
        if normalized in REPRESENTATION_TYPES:
            return normalized

    version = version_label.strip().lower() if isinstance(version_label, str) else ""
    if "original" in version or "master" in version:
        return "original_master"
    if "mobile" in version or "light" in version:
        return "mobile_lightweight"
    if "detail" in version or "research" in version or "high" in version:
        return "research_detail"
    if "web" in version or bool(is_web_preview and web_preview_status == "ready"):
        return "web_display"
    return "derivative"


def normalize_publication_status(value: str | None, *, preview_ready: bool = False) -> str:
    normalized = value.strip().lower() if isinstance(value, str) else ""
    if normalized in PUBLICATION_STATUSES:
        return normalized
    return "published" if preview_ready else "draft"


def build_digital_object_key(collection_object_id: int | None, resource_group: str) -> str:
    scope = str(collection_object_id) if collection_object_id is not None else "none"
    return f"collection:{scope}:group:{resource_group.strip()}"


def get_or_create_digital_object(
    db: Session,
    *,
    collection_object: ThreeDCollectionObject | None,
    resource_group: str,
    title: str,
    project_code: str | None = None,
    capture_batch: str | None = None,
    responsible_department: str | None = None,
) -> ThreeDDigitalObject:
    normalized_group = resource_group.strip() or title.strip()
    object_key = build_digital_object_key(
        collection_object.id if collection_object is not None else None,
        normalized_group,
    )
    digital_object = (
        db.query(ThreeDDigitalObject)
        .filter(ThreeDDigitalObject.object_key == object_key)
        .first()
    )
    if digital_object is None:
        digital_object = ThreeDDigitalObject(
            object_key=object_key,
            collection_object=collection_object,
            legacy_resource_group=normalized_group,
            title=title.strip() or normalized_group,
            project_code=_optional_text(project_code),
            capture_batch=_optional_text(capture_batch),
            responsible_department=_optional_text(responsible_department),
            lifecycle_status="draft",
            metadata_info={"created_from": "resource_group"},
        )
        db.add(digital_object)
        db.flush()
    else:
        digital_object.collection_object = collection_object
        if title.strip():
            digital_object.title = title.strip()
        if project_code is not None:
            digital_object.project_code = _optional_text(project_code)
        if capture_batch is not None:
            digital_object.capture_batch = _optional_text(capture_batch)
        if responsible_department is not None:
            digital_object.responsible_department = _optional_text(responsible_department)
    return digital_object
