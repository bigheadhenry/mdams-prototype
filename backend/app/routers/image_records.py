from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session
from PIL import Image

from .. import config
from ..database import get_db
from ..models import Asset, ImageIngestSheet, ImageRecord, User
from ..permissions import CurrentUser, require_any_permission, require_permission
from ..schemas import (
    CulturalObjectSampleListResponse,
    CulturalObjectLookupResponse,
    ImageIngestSheetDetailResponse,
    ImageIngestSheetSaveRequest,
    ImageIngestSheetSummary,
    ImageRecordActionRequest,
    ImageRecordAssetBinding,
    ImageRecordConfirmRequest,
    ImageRecordDetailResponse,
    ImageRecordDuplicateAssetMatch,
    ImageRecordPendingUpload,
    ImageRecordSaveRequest,
    ImageRecordSummary,
    ImageRecordValidationResult,
    ImageRecordValidationState,
)
from ..services.cultural_object_lookup import list_cultural_object_samples, lookup_cultural_object_by_number
from ..services.face_recognition import build_face_recognition_pending_state
from ..services.image_record_validation import (
    ALLOWED_UPLOAD_EXTENSIONS,
    validate_bound_image_record,
    validate_image_record_for_submit,
)
from ..services.iiif_access import (
    get_asset_iiif_access_file_path,
    mark_asset_derivative_pending,
    mark_asset_ready_with_original_access,
)
from ..services.metadata_layers import CORE_FIELD_LABELS, FIELD_LABELS, PROFILE_DEFINITIONS, build_metadata_layers, get_fixity_sha256
from ..tasks import generate_iiif_access_derivative, recognize_business_activity_faces
from ..utils.metadata import extract_metadata

router = APIRouter(prefix="/image-records", tags=["image-records"])

DEFAULT_RESOURCE_TYPE = "image_2d_cultural_object"
DEFAULT_VISIBILITY_SCOPE = "open"
DEFAULT_PROFILE_KEY = "other"
READY_STATUS = "ready_for_upload"
RETURNED_STATUS = "returned"
DRAFT_STATUS = "draft"
UPLOADED_PENDING_VALIDATION_STATUS = "uploaded_pending_validation"
PENDING_UPLOAD_KEY = "pending_upload"
SHEET_DRAFT_STATUS = "draft"
SHEET_IN_PROGRESS_STATUS = "in_progress"
SHEET_COMPLETED_STATUS = "completed"
UPLOAD_VISIBLE_STATUSES = {READY_STATUS, UPLOADED_PENDING_VALIDATION_STATUS}

SHEET_TO_PROFILE_KEY = {
    "movable_artifact": "movable_artifact",
    "immovable_artifact": "immovable_artifact",
    "business_activity": "business_activity",
    "ancient_tree": "ancient_tree",
    "archaeology": "archaeology",
    "art_photography": "art_photography",
    "panorama": "panorama",
    "other": "other",
}


def _clean_optional_text(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_optional_int(value: object | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _normalize_visibility_scope(value: object | None) -> str:
    normalized = (_clean_optional_text(value) or DEFAULT_VISIBILITY_SCOPE).lower()
    return normalized if normalized in {"open", "owner_only"} else DEFAULT_VISIBILITY_SCOPE


def _normalize_profile_key(value: object | None) -> str:
    normalized = (_clean_optional_text(value) or DEFAULT_PROFILE_KEY).lower()
    return normalized if normalized in PROFILE_DEFINITIONS else DEFAULT_PROFILE_KEY


def _normalize_image_type(value: object | None) -> str:
    normalized = (_clean_optional_text(value) or DEFAULT_PROFILE_KEY).lower()
    return normalized if normalized in SHEET_TO_PROFILE_KEY else DEFAULT_PROFILE_KEY


def _normalize_resource_type(value: object | None) -> str:
    return _clean_optional_text(value) or DEFAULT_RESOURCE_TYPE


def _normalize_json_dict(value: object | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {str(key): item for key, item in value.items()}


def _is_temporary_object_number(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    return normalized in {"暂无号", "暫無號", "无号", "無號", "none", "n/a", "na", "temp-none"}


def _field_label(field_key: str) -> str:
    return CORE_FIELD_LABELS.get(field_key) or FIELD_LABELS.get(field_key) or field_key.replace("_", " ").title()


def _record_layers(record: ImageRecord) -> dict[str, Any]:
    return record.metadata_info if isinstance(record.metadata_info, dict) else {}


def _management_section(record: ImageRecord) -> dict[str, Any]:
    management = _record_layers(record).get("management")
    return management if isinstance(management, dict) else {}


def _profile_fields(record: ImageRecord) -> dict[str, Any]:
    profile = _record_layers(record).get("profile")
    if not isinstance(profile, dict):
        return {}
    fields = profile.get("fields")
    return fields if isinstance(fields, dict) else {}


def _record_raw_metadata(record: ImageRecord) -> dict[str, Any]:
    raw_metadata = _record_layers(record).get("raw_metadata")
    return dict(raw_metadata) if isinstance(raw_metadata, dict) else {}


def _append_audit_entry(record: ImageRecord, action: str, actor: CurrentUser, note: str | None = None) -> None:
    layers = dict(_record_layers(record))
    raw_metadata = layers.get("raw_metadata")
    if not isinstance(raw_metadata, dict):
        raw_metadata = {}
    else:
        raw_metadata = dict(raw_metadata)
    audit_trail = raw_metadata.get("audit_trail")
    if not isinstance(audit_trail, list):
        audit_trail = []
    else:
        audit_trail = list(audit_trail)
    audit_trail.append(
        {
            "action": action,
            "actor": actor.display_name,
            "user_id": actor.user_id,
            "at": datetime.now(timezone.utc).isoformat(),
            "note": note,
        }
    )
    raw_metadata["audit_trail"] = audit_trail
    layers["raw_metadata"] = raw_metadata
    record.metadata_info = layers


def _find_user_entity(db: Session, actor: CurrentUser) -> User | None:
    return db.query(User).filter(User.username == actor.user_id, User.is_active.is_(True)).first()


def _current_user_db_id(db: Session, actor: CurrentUser) -> int | None:
    user = _find_user_entity(db, actor)
    return user.id if user is not None else None


def _sheet_metadata_info(sheet: ImageIngestSheet) -> dict[str, Any]:
    return sheet.metadata_info if isinstance(sheet.metadata_info, dict) else {}


def _get_sheet_or_404(sheet_id: int, db: Session) -> ImageIngestSheet:
    sheet = db.query(ImageIngestSheet).filter(ImageIngestSheet.id == sheet_id).first()
    if sheet is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image ingest sheet not found")
    return sheet


def _sheet_management_defaults(sheet: ImageIngestSheet) -> dict[str, Any]:
    return {
        "project_type": sheet.project_type,
        "project_name": sheet.project_name,
        "photographer": sheet.photographer,
        "photographer_org": sheet.photographer_org,
        "copyright_owner": sheet.copyright_owner,
        "capture_time": sheet.capture_time,
        "image_category": sheet.image_type,
        "remark": sheet.remark,
    }


def _sync_sheet_values_to_record_management(record: ImageRecord, sheet: ImageIngestSheet) -> None:
    management = {
        **_management_section(record),
        **{key: value for key, value in _sheet_management_defaults(sheet).items() if value not in (None, "")},
    }
    raw_metadata = _record_layers(record).get("raw_metadata")
    if not isinstance(raw_metadata, dict):
        raw_metadata = {}
    record.metadata_info = _build_layers(
        record_no=record.record_no,
        title=record.title,
        status_code=record.status,
        resource_type=record.resource_type,
        visibility_scope=record.visibility_scope,
        collection_object_id=record.collection_object_id,
        profile_key=record.profile_key,
        management=management,
        profile_fields=_profile_fields(record),
        raw_metadata=raw_metadata,
    )


def _next_sheet_line_no(sheet: ImageIngestSheet) -> int:
    existing = [item.line_no or 0 for item in sheet.items]
    return (max(existing) if existing else 0) + 1


def _sheet_status(sheet: ImageIngestSheet) -> str:
    if not sheet.items:
        return SHEET_DRAFT_STATUS
    statuses = {item.status for item in sheet.items if item.status}
    if statuses and statuses <= {UPLOADED_PENDING_VALIDATION_STATUS}:
        return SHEET_COMPLETED_STATUS
    if READY_STATUS in statuses or UPLOADED_PENDING_VALIDATION_STATUS in statuses:
        return SHEET_IN_PROGRESS_STATUS
    return SHEET_IN_PROGRESS_STATUS


def _is_sheet_visible_to_user(sheet: ImageIngestSheet, user: CurrentUser) -> bool:
    if user.has_permission("image.record.list"):
        return True
    if not user.has_permission("image.record.view_ready_for_upload"):
        return False

    user_db_id = user.user_id
    if sheet.assigned_photographer_user is not None and sheet.assigned_photographer_user.username == user_db_id:
        return True

    return any(
        item.assigned_photographer_user is not None and item.assigned_photographer_user.username == user_db_id
        for item in sheet.items
    )


def _is_record_assigned_to_user(record: ImageRecord, user: CurrentUser) -> bool:
    user_db_id = user.user_id
    if record.assigned_photographer_user is not None and record.assigned_photographer_user.username == user_db_id:
        return True
    if (
        record.sheet is not None
        and record.sheet.assigned_photographer_user is not None
        and record.sheet.assigned_photographer_user.username == user_db_id
    ):
        return True
    return False


def _visible_sheet_items_for_user(sheet: ImageIngestSheet, user: CurrentUser | None = None) -> list[ImageRecord]:
    items = list(sheet.items or [])
    if user is None or user.has_permission("image.record.list"):
        return items
    if not user.has_permission("image.record.view_ready_for_upload"):
        return []
    return [
        item
        for item in items
        if item.status in UPLOAD_VISIBLE_STATUSES and _is_record_assigned_to_user(item, user)
    ]


def _serialize_sheet_summary(sheet: ImageIngestSheet) -> ImageIngestSheetSummary:
    items = list(sheet.items or [])
    uploaded_count = sum(1 for item in items if item.status in {UPLOADED_PENDING_VALIDATION_STATUS})
    return ImageIngestSheetSummary(
        id=sheet.id,
        sheet_no=sheet.sheet_no,
        title=sheet.title,
        status=_sheet_status(sheet),
        image_type=sheet.image_type,
        project_type=sheet.project_type,
        project_name=sheet.project_name,
        photographer=sheet.photographer,
        photographer_org=sheet.photographer_org,
        capture_time=sheet.capture_time,
        assigned_photographer_user_id=sheet.assigned_photographer_user_id,
        assigned_photographer_display_name=getattr(sheet.assigned_photographer_user, "display_name", None),
        item_count=len(items),
        uploaded_item_count=uploaded_count,
        created_at=sheet.created_at,
        updated_at=sheet.updated_at,
    )


def _serialize_sheet_detail(sheet: ImageIngestSheet, user: CurrentUser | None = None) -> ImageIngestSheetDetailResponse:
    summary = _serialize_sheet_summary(sheet)
    return ImageIngestSheetDetailResponse(
        **summary.model_dump(),
        copyright_owner=sheet.copyright_owner,
        remark=sheet.remark,
        metadata_info=_sheet_metadata_info(sheet),
        items=[_serialize_image_record(item) for item in _visible_sheet_items_for_user(sheet, user)],
    )


def _pending_upload_data(record: ImageRecord) -> dict[str, Any] | None:
    raw_metadata = _record_layers(record).get("raw_metadata")
    if not isinstance(raw_metadata, dict):
        return None
    pending_upload = raw_metadata.get(PENDING_UPLOAD_KEY)
    return dict(pending_upload) if isinstance(pending_upload, dict) else None


def _set_pending_upload(record: ImageRecord, payload: dict[str, Any] | None) -> None:
    layers = dict(_record_layers(record))
    raw_metadata = layers.get("raw_metadata")
    if not isinstance(raw_metadata, dict):
        raw_metadata = {}
    else:
        raw_metadata = dict(raw_metadata)

    if payload is None:
        raw_metadata.pop(PENDING_UPLOAD_KEY, None)
    else:
        raw_metadata[PENDING_UPLOAD_KEY] = payload

    layers["raw_metadata"] = raw_metadata
    record.metadata_info = layers


def _cleanup_pending_upload_file(record: ImageRecord) -> None:
    pending_upload = _pending_upload_data(record)
    if pending_upload is None:
        return

    temp_path = _clean_optional_text(pending_upload.get("temp_path"))
    if temp_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except OSError:
            pass


def _clear_pending_upload(record: ImageRecord) -> None:
    _cleanup_pending_upload_file(record)
    _set_pending_upload(record, None)


def _record_search_text(record: ImageRecord) -> str:
    management = _management_section(record)
    profile_fields = _profile_fields(record)
    tokens = [
        record.record_no,
        record.title,
        management.get("project_name"),
        management.get("image_name"),
        profile_fields.get("object_number"),
    ]
    return " ".join(str(token).lower() for token in tokens if token not in (None, ""))


def _matches_query(record: ImageRecord, normalized_query: str | None) -> bool:
    if not normalized_query:
        return True
    return normalized_query.lower() in _record_search_text(record)


def _duplicate_assets_for_hash(db: Session, sha256: str) -> list[Asset]:
    if not sha256:
        return []
    matches: list[Asset] = []
    for asset in db.query(Asset).order_by(Asset.id.asc()).all():
        if get_fixity_sha256(asset.metadata_info) == sha256:
            matches.append(asset)
    return matches


def _serialize_pending_upload(record: ImageRecord) -> ImageRecordPendingUpload | None:
    pending_upload = _pending_upload_data(record)
    if pending_upload is None:
        return None

    validation = _validation_result_from_dict(pending_upload.get("validation"))

    duplicate_assets = [
        ImageRecordDuplicateAssetMatch(
            asset_id=int(item.get("asset_id")),
            filename=_clean_optional_text(item.get("filename")),
            image_record_id=_normalize_optional_int(item.get("image_record_id")),
            status=_clean_optional_text(item.get("status")),
        )
        for item in pending_upload.get("duplicate_assets", [])
        if isinstance(item, dict) and _normalize_optional_int(item.get("asset_id")) is not None
    ]

    uploaded_at_raw = pending_upload.get("uploaded_at")
    uploaded_at = datetime.now(timezone.utc)
    if isinstance(uploaded_at_raw, str):
        try:
            uploaded_at = datetime.fromisoformat(uploaded_at_raw)
        except ValueError:
            uploaded_at = datetime.now(timezone.utc)

    return ImageRecordPendingUpload(
        token=str(pending_upload.get("token") or ""),
        filename=str(pending_upload.get("filename") or ""),
        file_size=int(pending_upload.get("file_size") or 0),
        mime_type=_clean_optional_text(pending_upload.get("mime_type")),
        extension=_clean_optional_text(pending_upload.get("extension")),
        width=_normalize_optional_int(pending_upload.get("width")),
        height=_normalize_optional_int(pending_upload.get("height")),
        format_name=_clean_optional_text(pending_upload.get("format_name")),
        sha256=str(pending_upload.get("sha256") or ""),
        uploaded_at=uploaded_at,
        filename_matches=[str(item) for item in pending_upload.get("filename_matches", []) if str(item).strip()],
        warnings=[str(item) for item in pending_upload.get("warnings", []) if str(item).strip()],
        duplicate_assets=duplicate_assets,
        validation=validation,
        can_confirm_bind=not bool(record.asset) and not (validation.has_blocking_errors if validation else False),
        can_confirm_replace=bool(record.asset) and not (validation.has_blocking_errors if validation else False),
    )


def _serialize_duplicate_assets(assets: list[Asset]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for asset in assets:
        serialized.append(
            {
                "asset_id": asset.id,
                "filename": asset.filename,
                "image_record_id": asset.image_record_id,
                "status": asset.status,
            }
        )
    return serialized


def _replace_current_asset_binding(record: ImageRecord, actor: CurrentUser, note: str | None = None) -> Asset:
    current_asset = record.asset
    if current_asset is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image record does not have an active asset to replace")

    current_asset.image_record_id = None
    current_asset.status = "superseded"

    metadata_info = current_asset.metadata_info if isinstance(current_asset.metadata_info, dict) else {}
    raw_metadata = metadata_info.get("raw_metadata") if isinstance(metadata_info.get("raw_metadata"), dict) else {}
    history = raw_metadata.get("replacement_history")
    if not isinstance(history, list):
        history = []
    else:
        history = list(history)
    history.append(
        {
            "replaced_at": datetime.now(timezone.utc).isoformat(),
            "replaced_by_user_id": actor.user_id,
            "note": note,
            "image_record_id": record.id,
        }
    )
    raw_metadata = dict(raw_metadata)
    raw_metadata["replacement_history"] = history
    metadata_info = dict(metadata_info)
    metadata_info["raw_metadata"] = raw_metadata
    current_asset.metadata_info = metadata_info
    current_asset.process_message = "Superseded by image record replacement"
    return current_asset


def _record_no_is_unique(db: Session, record_no: str, record_id: int | None = None) -> bool:
    query = db.query(ImageRecord).filter(ImageRecord.record_no == record_no)
    if record_id is not None:
        query = query.filter(ImageRecord.id != record_id)
    return query.first() is None


def _validation_state(record: ImageRecord, db: Session) -> ImageRecordValidationState:
    return validate_image_record_for_submit(
        record,
        record_no_is_unique=_record_no_is_unique(db, record.record_no, record.id),
    )


def _validation_result_from_dict(value: object | None) -> ImageRecordValidationResult | None:
    if not isinstance(value, dict):
        return None
    try:
        return ImageRecordValidationResult.model_validate(value)
    except Exception:
        return None


def _stored_binding_validation(record: ImageRecord) -> ImageRecordValidationResult | None:
    raw_metadata = _record_layers(record).get("raw_metadata")
    if not isinstance(raw_metadata, dict):
        return None
    return _validation_result_from_dict(raw_metadata.get("binding_validation"))


def _set_binding_validation(record: ImageRecord, result: ImageRecordValidationResult) -> None:
    layers = dict(_record_layers(record))
    raw_metadata = layers.get("raw_metadata")
    if not isinstance(raw_metadata, dict):
        raw_metadata = {}
    else:
        raw_metadata = dict(raw_metadata)
    raw_metadata["binding_validation"] = result.model_dump()
    layers["raw_metadata"] = raw_metadata
    record.metadata_info = layers


def _serialize_image_record(record: ImageRecord) -> ImageRecordSummary:
    layers = _record_layers(record)
    management = _management_section(record)
    profile = layers.get("profile") if isinstance(layers.get("profile"), dict) else {}
    profile_fields = _profile_fields(record)

    asset = None
    if record.asset is not None:
        asset = ImageRecordAssetBinding(
            asset_id=record.asset.id,
            filename=record.asset.filename,
            status=record.asset.status,
            created_at=record.asset.created_at,
        )

    return ImageRecordSummary(
        id=record.id,
        sheet_id=record.sheet_id,
        line_no=record.line_no,
        record_no=record.record_no,
        title=record.title or record.record_no,
        status=record.status,
        resource_type=record.resource_type,
        visibility_scope=record.visibility_scope,
        collection_object_id=record.collection_object_id,
        profile_key=record.profile_key,
        profile_label=str(profile.get("label") or PROFILE_DEFINITIONS.get(record.profile_key, PROFILE_DEFINITIONS[DEFAULT_PROFILE_KEY])["label"]),
        project_name=_clean_optional_text(management.get("project_name")),
        image_category=_clean_optional_text(management.get("image_category")),
        object_number=_clean_optional_text(profile_fields.get("object_number")),
        representative_image=bool(management.get("representative_image")),
        created_by_user_id=record.created_by_user_id,
        created_by_display_name=getattr(record.created_by_user, "display_name", None),
        submitted_by_user_id=record.submitted_by_user_id,
        submitted_by_display_name=getattr(record.submitted_by_user, "display_name", None),
        assigned_photographer_user_id=record.assigned_photographer_user_id,
        assigned_photographer_display_name=getattr(record.assigned_photographer_user, "display_name", None),
        created_at=record.created_at,
        updated_at=record.updated_at,
        submitted_at=record.submitted_at,
        asset=asset,
    )


def _serialize_image_record_detail(record: ImageRecord, db: Session) -> ImageRecordDetailResponse:
    summary = _serialize_image_record(record)
    return ImageRecordDetailResponse(
        **summary.model_dump(),
        metadata_info=_record_layers(record),
        validation=_validation_state(record, db),
        pending_upload=_serialize_pending_upload(record),
        binding_validation=_stored_binding_validation(record),
    )


def _ensure_record_no_unique(db: Session, record_no: str, record_id: int | None = None) -> None:
    query = db.query(ImageRecord).filter(ImageRecord.record_no == record_no)
    if record_id is not None:
        query = query.filter(ImageRecord.id != record_id)
    if query.first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Image record number already exists")


def _get_image_record_or_404(record_id: int, db: Session) -> ImageRecord:
    record = db.query(ImageRecord).filter(ImageRecord.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image record not found")
    return record


def _is_visible_to_user(record: ImageRecord, user: CurrentUser) -> bool:
    if user.has_permission("image.record.list"):
        return True
    return (
        user.has_permission("image.record.view_ready_for_upload")
        and record.status in UPLOAD_VISIBLE_STATUSES
        and _is_record_assigned_to_user(record, user)
    )


def _get_accessible_image_record(record_id: int, db: Session, user: CurrentUser) -> ImageRecord:
    record = _get_image_record_or_404(record_id, db)
    if not _is_visible_to_user(record, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Image record is not visible to current user")
    return record


def _get_photographer_if_valid(db: Session, photographer_user_id: int | None) -> User | None:
    if photographer_user_id is None:
        return None
    photographer = db.query(User).filter(User.id == photographer_user_id, User.is_active.is_(True)).first()
    if photographer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned photographer user not found")
    photographer_roles = {user_role.role.key for user_role in photographer.roles if user_role.role is not None}
    if "image_photographer_upload" not in photographer_roles and "system_admin" not in photographer_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assigned user is not a photographer upload role")
    return photographer


def _apply_sheet_payload(
    sheet: ImageIngestSheet,
    payload: ImageIngestSheetSaveRequest,
    db: Session,
    actor: CurrentUser,
) -> None:
    if "image_type" in payload.model_fields_set and sheet.items:
        next_image_type = _normalize_image_type(payload.image_type)
        if next_image_type != sheet.image_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change image type after sheet items have been created",
            )

    photographer_user_id = (
        _normalize_optional_int(payload.assigned_photographer_user_id)
        if "assigned_photographer_user_id" in payload.model_fields_set
        else sheet.assigned_photographer_user_id
    )
    photographer = _get_photographer_if_valid(db, photographer_user_id)

    if "title" in payload.model_fields_set:
        sheet.title = _clean_optional_text(payload.title)
    if "image_type" in payload.model_fields_set:
        sheet.image_type = _normalize_image_type(payload.image_type)
    if "project_type" in payload.model_fields_set:
        sheet.project_type = _clean_optional_text(payload.project_type)
    if "project_name" in payload.model_fields_set:
        sheet.project_name = _clean_optional_text(payload.project_name)
    if "photographer" in payload.model_fields_set:
        sheet.photographer = _clean_optional_text(payload.photographer)
    if "photographer_org" in payload.model_fields_set:
        sheet.photographer_org = _clean_optional_text(payload.photographer_org)
    if "copyright_owner" in payload.model_fields_set:
        sheet.copyright_owner = _clean_optional_text(payload.copyright_owner)
    if "capture_time" in payload.model_fields_set:
        sheet.capture_time = _clean_optional_text(payload.capture_time)
    if "remark" in payload.model_fields_set:
        sheet.remark = _clean_optional_text(payload.remark)
    if "metadata_info" in payload.model_fields_set:
        sheet.metadata_info = _normalize_json_dict(payload.metadata_info)
    sheet.assigned_photographer_user_id = photographer.id if photographer else None
    sheet.status = _sheet_status(sheet)

    for item in sheet.items:
        _sync_sheet_values_to_record_management(item, sheet)


def _build_layers(
    *,
    record_no: str,
    title: str | None,
    status_code: str,
    resource_type: str,
    visibility_scope: str,
    collection_object_id: int | None,
    profile_key: str,
    management: dict[str, Any],
    profile_fields: dict[str, Any],
    raw_metadata: dict[str, Any],
) -> dict[str, Any]:
    layered_source = {
        "core": {
            "record_no": record_no,
            "title": title,
            "status": status_code,
            "resource_type": resource_type,
            "visibility_scope": visibility_scope,
            "collection_object_id": collection_object_id,
            "profile_key": profile_key,
        },
        "management": management,
        "profile": {
            "key": profile_key,
            "fields": profile_fields,
        },
        "raw_metadata": raw_metadata,
    }
    layers = build_metadata_layers(
        asset_status=status_code,
        asset_resource_type=resource_type,
        asset_visibility_scope=visibility_scope,
        asset_collection_object_id=collection_object_id,
        metadata=layered_source,
        source_metadata=raw_metadata,
        profile_hint=profile_key,
    )
    layers["core"]["record_no"] = record_no
    return layers


def _apply_record_payload(
    record: ImageRecord,
    payload: ImageRecordSaveRequest,
    db: Session,
    actor: CurrentUser,
) -> None:
    normalized_record_no = _clean_optional_text(payload.record_no)
    if normalized_record_no:
        _ensure_record_no_unique(db, normalized_record_no, record.id if record.id else None)
        record.record_no = normalized_record_no

    photographer_user_id = (
        _normalize_optional_int(payload.assigned_photographer_user_id)
        if "assigned_photographer_user_id" in payload.model_fields_set
        else record.assigned_photographer_user_id
    )
    photographer = _get_photographer_if_valid(db, photographer_user_id)

    management = {
        **_management_section(record),
        **_normalize_json_dict(payload.management),
    }
    profile_fields = {
        **_profile_fields(record),
        **_normalize_json_dict(payload.profile_fields),
    }
    raw_metadata = {
        **(_record_layers(record).get("raw_metadata") if isinstance(_record_layers(record).get("raw_metadata"), dict) else {}),
        **_normalize_json_dict(payload.raw_metadata),
    }
    now_iso = datetime.now(timezone.utc).isoformat()
    management.setdefault("record_account", actor.display_name)
    management.setdefault("record_time", now_iso)

    if "title" in payload.model_fields_set:
        record.title = _clean_optional_text(payload.title)
    if "resource_type" in payload.model_fields_set:
        record.resource_type = _normalize_resource_type(payload.resource_type)
    if "visibility_scope" in payload.model_fields_set:
        record.visibility_scope = _normalize_visibility_scope(payload.visibility_scope)
    if "collection_object_id" in payload.model_fields_set:
        record.collection_object_id = _normalize_optional_int(payload.collection_object_id)
    if "profile_key" in payload.model_fields_set:
        record.profile_key = _normalize_profile_key(payload.profile_key)
    record.assigned_photographer_user_id = photographer.id if photographer else None
    record.metadata_info = _build_layers(
        record_no=record.record_no,
        title=record.title,
        status_code=record.status,
        resource_type=record.resource_type,
        visibility_scope=record.visibility_scope,
        collection_object_id=record.collection_object_id,
        profile_key=record.profile_key,
        management=management,
        profile_fields=profile_fields,
        raw_metadata=raw_metadata,
    )


def _set_record_status(record: ImageRecord, status_code: str) -> None:
    record.status = status_code
    layers = dict(_record_layers(record))
    core = layers.get("core")
    if not isinstance(core, dict):
        core = {}
    else:
        core = dict(core)
    core["status"] = status_code
    layers["core"] = core
    record.metadata_info = layers


def _set_representative_image_flag_in_layers(layers: dict[str, Any], value: bool) -> dict[str, Any]:
    next_layers = dict(layers)
    management = next_layers.get("management")
    if not isinstance(management, dict):
        management = {}
    else:
        management = dict(management)
    management["representative_image"] = value
    next_layers["management"] = management
    return next_layers


def _enforce_unique_representative_image(record: ImageRecord, db: Session) -> None:
    if record.profile_key != "movable_artifact":
        return

    management = _management_section(record)
    if not bool(management.get("representative_image")):
        return

    object_number = _clean_optional_text(_profile_fields(record).get("object_number"))
    if not object_number or _is_temporary_object_number(object_number):
        return

    candidate_records = (
        db.query(ImageRecord)
        .filter(ImageRecord.id != record.id, ImageRecord.profile_key == "movable_artifact")
        .all()
    )

    for other_record in candidate_records:
        other_profile_fields = _profile_fields(other_record)
        if _clean_optional_text(other_profile_fields.get("object_number")) != object_number:
            continue

        other_management = _management_section(other_record)
        if not bool(other_management.get("representative_image")):
            continue

        other_layers = _set_representative_image_flag_in_layers(_record_layers(other_record), False)
        other_record.metadata_info = other_layers

        if other_record.asset is not None and isinstance(other_record.asset.metadata_info, dict):
            other_record.asset.metadata_info = _set_representative_image_flag_in_layers(other_record.asset.metadata_info, False)


def _temp_upload_dir() -> str:
    directory = os.path.join(config.UPLOAD_DIR, "image-record-temp")
    os.makedirs(directory, exist_ok=True)
    return directory


async def _write_upload_file(destination_path: str, upload_file: UploadFile) -> int:
    written = 0
    with open(destination_path, "wb") as buffer:
        while content := await upload_file.read(64 * 1024):
            buffer.write(content)
            written += len(content)
    return written


def _compute_file_sha256(file_path: str) -> str:
    digest = hashlib.sha256()
    with open(file_path, "rb") as handle:
        while chunk := handle.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_probe_dimensions(metadata: dict[str, Any]) -> tuple[int | None, int | None, str | None]:
    file_group = metadata.get("File")
    if not isinstance(file_group, dict):
        file_group = {}

    width = _normalize_optional_int(file_group.get("ImageWidth"))
    height = _normalize_optional_int(file_group.get("ImageHeight"))
    format_name = _clean_optional_text(file_group.get("MIMEType")) or _clean_optional_text(file_group.get("FileType"))

    if width is not None and height is not None:
        return width, height, format_name

    composite_group = metadata.get("Composite")
    if not isinstance(composite_group, dict):
        composite_group = {}

    image_size = _clean_optional_text(composite_group.get("ImageSize"))
    if image_size and "x" in image_size.lower():
        width_text, height_text = image_size.lower().split("x", 1)
        width = _normalize_optional_int(width_text)
        height = _normalize_optional_int(height_text)

    return width, height, format_name


def _probe_image_file(file_path: str, fallback_mime_type: str | None) -> tuple[int | None, int | None, str | None, int | None]:
    width: int | None = None
    height: int | None = None
    format_name: str | None = fallback_mime_type
    frame_count: int | None = None
    try:
        with Image.open(file_path) as image:
            width, height = image.size
            format_name = image.format or fallback_mime_type
            frame_count = int(getattr(image, "n_frames", 1) or 1)
    except Exception:
        pass

    if width is None or height is None:
        exif_metadata = extract_metadata(file_path)
        metadata_width, metadata_height, metadata_format_name = _extract_probe_dimensions(exif_metadata)
        if metadata_width is not None:
            width = metadata_width
        if metadata_height is not None:
            height = metadata_height
        if metadata_format_name:
            format_name = metadata_format_name

    if width is None or height is None:
        try:
            import pyvips

            image = pyvips.Image.new_from_file(file_path, access="sequential")
            width = width or int(image.width or 0) or None
            height = height or int(image.height or 0) or None
            if not format_name and image.format:
                format_name = str(image.format)
        except Exception:
            pass

    return width, height, format_name, frame_count


def _apply_asset_access_strategy(asset: Asset) -> None:
    if get_asset_iiif_access_file_path(asset, allow_original_fallback=False):
        mark_asset_ready_with_original_access(asset)
    else:
        mark_asset_derivative_pending(asset)


def _enqueue_asset_derivative_generation(asset: Asset) -> None:
    if asset.status == "processing" and asset.file_path:
        generate_iiif_access_derivative.delay(asset.id, asset.file_path)


def _set_face_recognition_pending(record: ImageRecord, asset: Asset) -> None:
    if record.profile_key != "business_activity" or not config.FACE_RECOGNITION_ENABLED:
        return

    face_recognition = build_face_recognition_pending_state(
        asset_id=asset.id,
        threshold=config.FACE_RECOGNITION_THRESHOLD,
    )

    raw_metadata = _record_raw_metadata(record)
    raw_metadata["face_recognition"] = face_recognition
    profile_fields = dict(_profile_fields(record))
    profile_fields.pop("main_person", None)
    record.metadata_info = _build_layers(
        record_no=record.record_no,
        title=record.title,
        status_code=record.status,
        resource_type=record.resource_type,
        visibility_scope=record.visibility_scope,
        collection_object_id=record.collection_object_id,
        profile_key=record.profile_key,
        management=_management_section(record),
        profile_fields=profile_fields,
        raw_metadata=raw_metadata,
    )

    asset_layers = build_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_visibility_scope=asset.visibility_scope,
        asset_collection_object_id=asset.collection_object_id,
        asset_created_at=asset.created_at,
        metadata=asset.metadata_info or {},
        source_metadata={
            **(
                asset.metadata_info.get("raw_metadata", {})
                if isinstance(asset.metadata_info, dict) and isinstance(asset.metadata_info.get("raw_metadata"), dict)
                else {}
            ),
            "face_recognition": face_recognition,
        },
        profile_hint=record.profile_key,
    )
    asset.metadata_info = asset_layers


def _enqueue_business_activity_face_recognition(record: ImageRecord, asset: Asset) -> None:
    if record.profile_key != "business_activity" or not config.FACE_RECOGNITION_ENABLED:
        return
    recognize_business_activity_faces.delay(record.id, asset.id)


def _build_pending_upload_payload(
    record: ImageRecord,
    asset_file: UploadFile,
    file_path: str,
    file_size: int,
    db: Session,
    actor: CurrentUser,
) -> dict[str, Any]:
    original_filename = os.path.basename(asset_file.filename or "upload.bin")
    extension = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else ""
    sha256 = _compute_file_sha256(file_path)
    width, height, format_name, frame_count = _probe_image_file(file_path, asset_file.content_type)

    filename_matches: list[str] = []
    lowered_filename = original_filename.lower()
    if record.record_no.lower() in lowered_filename:
        filename_matches.append(f"record_no:{record.record_no}")
    object_number = _clean_optional_text(_profile_fields(record).get("object_number"))
    if object_number and object_number.lower() in lowered_filename:
        filename_matches.append(f"object_number:{object_number}")

    duplicate_assets = _duplicate_assets_for_hash(db, sha256)
    validation = validate_bound_image_record(
        record,
        {
            "filename": original_filename,
            "extension": extension or None,
            "file_size": file_size,
            "width": width,
            "height": height,
            "format_name": format_name,
            "frame_count": frame_count,
            "sha256": sha256,
        },
        duplicate_assets,
        actor,
    )

    return {
        "token": secrets.token_urlsafe(16),
        "filename": original_filename,
        "temp_path": file_path,
        "file_size": file_size,
        "mime_type": asset_file.content_type,
        "extension": extension or None,
        "width": width,
        "height": height,
        "format_name": format_name,
        "frame_count": frame_count,
        "sha256": sha256,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "filename_matches": filename_matches,
        "warnings": [rule.message for rule in validation.validation_report if rule.level == "warning"],
        "validation": validation.model_dump(),
        "duplicate_assets": _serialize_duplicate_assets(duplicate_assets),
    }


def _revalidate_pending_upload(
    record: ImageRecord,
    pending_upload: dict[str, Any],
    db: Session,
    actor: CurrentUser,
) -> ImageRecordValidationResult:
    duplicate_assets = _duplicate_assets_for_hash(db, str(pending_upload.get("sha256") or ""))
    validation = validate_bound_image_record(record, pending_upload, duplicate_assets, actor)
    pending_upload["duplicate_assets"] = _serialize_duplicate_assets(duplicate_assets)
    pending_upload["warnings"] = [rule.message for rule in validation.validation_report if rule.level == "warning"]
    pending_upload["validation"] = validation.model_dump()
    return validation


def _build_asset_metadata_from_pending_upload(record: ImageRecord, pending_upload: dict[str, Any], actor: CurrentUser) -> dict[str, Any]:
    base_metadata = {
        "title": record.title or record.record_no,
        "record_no": record.record_no,
        "image_record_id": record.id,
        "ingest_method": "image_record_confirmed_upload",
        "original_file_name": pending_upload.get("filename"),
        "image_file_name": pending_upload.get("filename"),
        "file_size": pending_upload.get("file_size"),
        "format_name": pending_upload.get("format_name") or pending_upload.get("mime_type"),
        "width": pending_upload.get("width"),
        "height": pending_upload.get("height"),
        "fixity_sha256": pending_upload.get("sha256"),
        "checksum": pending_upload.get("sha256"),
        "checksum_algorithm": "SHA256",
        "visibility_scope": record.visibility_scope,
        "collection_object_id": record.collection_object_id,
    }
    return build_metadata_layers(
        asset_filename=str(pending_upload.get("filename") or ""),
        asset_file_path=str(pending_upload.get("temp_path") or ""),
        asset_file_size=_normalize_optional_int(pending_upload.get("file_size")),
        asset_mime_type=_clean_optional_text(pending_upload.get("mime_type")),
        asset_status="processing",
        asset_resource_type=record.resource_type,
        asset_visibility_scope=record.visibility_scope,
        asset_collection_object_id=record.collection_object_id,
        metadata={
            **base_metadata,
            "management": _management_section(record),
            "profile": {
                "key": record.profile_key,
                "fields": _profile_fields(record),
            },
        },
        source_metadata={
            "image_record_id": record.id,
            "record_no": record.record_no,
            "confirmed_by_user_id": actor.user_id,
            "confirmed_at": datetime.now(timezone.utc).isoformat(),
            "pending_upload": {
                "filename_matches": list(pending_upload.get("filename_matches", [])),
                "warnings": list(pending_upload.get("warnings", [])),
                "sha256": pending_upload.get("sha256"),
                "validation": pending_upload.get("validation"),
            },
        },
        profile_hint=record.profile_key,
    )


def _assert_confirm_token(record: ImageRecord, payload: ImageRecordConfirmRequest) -> dict[str, Any]:
    pending_upload = _pending_upload_data(record)
    if pending_upload is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image record does not have a pending upload to confirm")
    if pending_upload.get("token") != payload.temp_upload_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pending upload token is invalid or expired")
    temp_path = _clean_optional_text(pending_upload.get("temp_path"))
    if not temp_path or not os.path.exists(temp_path):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pending upload file is no longer available")
    return pending_upload


@router.get("/ready-for-upload", response_model=list[ImageRecordSummary])
def list_ready_for_upload_records(
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.view_ready_for_upload")),
):
    query = db.query(ImageRecord).filter(ImageRecord.status == READY_STATUS)
    if not user.has_permission("image.record.list"):
        photographer = _find_user_entity(db, user)
        if photographer is None:
            return []
        query = query.filter(ImageRecord.assigned_photographer_user_id == photographer.id)

    records = query.order_by(ImageRecord.submitted_at.desc(), ImageRecord.updated_at.desc(), ImageRecord.id.desc()).all()
    normalized_q = _clean_optional_text(q)
    visible_records = [record for record in records if _matches_query(record, normalized_q)]
    return [_serialize_image_record(record) for record in visible_records[skip : skip + limit]]


@router.get("/artifact-lookup", response_model=CulturalObjectLookupResponse)
def lookup_cultural_object(
    object_number: str = Query(..., min_length=1),
    user: CurrentUser = Depends(require_permission("image.record.view")),
):
    try:
        return lookup_cultural_object_by_number(object_number)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/artifact-samples", response_model=CulturalObjectSampleListResponse)
def list_artifact_samples(
    q: str | None = None,
    limit: int = Query(100, ge=1, le=100),
    user: CurrentUser = Depends(require_permission("image.record.view")),
):
    return list_cultural_object_samples(q=q, limit=limit)


@router.get("/sheets", response_model=list[ImageIngestSheetSummary])
def list_image_ingest_sheets(
    q: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_any_permission("image.record.list", "image.record.view_ready_for_upload")),
):
    normalized_q = _clean_optional_text(q)
    sheets = db.query(ImageIngestSheet).order_by(ImageIngestSheet.updated_at.desc(), ImageIngestSheet.id.desc()).all()
    visible: list[ImageIngestSheet] = []
    for sheet in sheets:
        if not _is_sheet_visible_to_user(sheet, user):
            continue
        if normalized_q:
            haystack = " ".join(
                filter(
                    None,
                    [
                        sheet.sheet_no,
                        sheet.title,
                        sheet.project_name,
                        sheet.project_type,
                        sheet.photographer,
                    ],
                )
            ).lower()
            if normalized_q.lower() not in haystack:
                continue
        visible.append(sheet)
    return [_serialize_sheet_summary(sheet) for sheet in visible]


@router.post("/sheets", response_model=ImageIngestSheetDetailResponse, status_code=status.HTTP_201_CREATED)
def create_image_ingest_sheet(
    payload: ImageIngestSheetSaveRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.create")),
):
    creator = _find_user_entity(db, user)
    sheet = ImageIngestSheet(
        sheet_no="PENDING",
        title=None,
        status=SHEET_DRAFT_STATUS,
        image_type=DEFAULT_PROFILE_KEY,
        metadata_info={},
        created_by_user_id=creator.id if creator is not None else None,
    )
    db.add(sheet)
    db.flush()
    sheet.sheet_no = f"IS-{datetime.now(timezone.utc):%Y%m%d}-{sheet.id:06d}"
    _apply_sheet_payload(sheet, payload, db, user)
    db.commit()
    db.refresh(sheet)
    return _serialize_sheet_detail(sheet, user)


@router.get("/sheets/{sheet_id}", response_model=ImageIngestSheetDetailResponse)
def get_image_ingest_sheet(
    sheet_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.view")),
):
    sheet = _get_sheet_or_404(sheet_id, db)
    if not _is_sheet_visible_to_user(sheet, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Image ingest sheet is not visible to current user")
    return _serialize_sheet_detail(sheet, user)


@router.patch("/sheets/{sheet_id}", response_model=ImageIngestSheetDetailResponse)
def update_image_ingest_sheet(
    sheet_id: int,
    payload: ImageIngestSheetSaveRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.edit")),
):
    sheet = _get_sheet_or_404(sheet_id, db)
    _apply_sheet_payload(sheet, payload, db, user)
    db.commit()
    db.refresh(sheet)
    return _serialize_sheet_detail(sheet, user)


@router.post("/sheets/{sheet_id}/items", response_model=ImageRecordDetailResponse, status_code=status.HTTP_201_CREATED)
def create_image_ingest_sheet_item(
    sheet_id: int,
    payload: ImageRecordSaveRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.create")),
):
    sheet = _get_sheet_or_404(sheet_id, db)
    creator = _find_user_entity(db, user)
    record = ImageRecord(
        sheet_id=sheet.id,
        line_no=_next_sheet_line_no(sheet),
        record_no="PENDING",
        title=None,
        status=DRAFT_STATUS,
        resource_type=DEFAULT_RESOURCE_TYPE,
        visibility_scope=DEFAULT_VISIBILITY_SCOPE,
        collection_object_id=None,
        profile_key=sheet.image_type,
        metadata_info={},
        created_by_user_id=creator.id if creator is not None else None,
        assigned_photographer_user_id=sheet.assigned_photographer_user_id,
    )
    db.add(record)
    db.flush()
    if not _clean_optional_text(payload.record_no):
        record.record_no = f"IR-{datetime.now(timezone.utc):%Y%m%d}-{record.id:06d}"

    merged_payload = ImageRecordSaveRequest(
        record_no=payload.record_no,
        title=payload.title,
        resource_type=payload.resource_type or DEFAULT_RESOURCE_TYPE,
        visibility_scope=payload.visibility_scope or DEFAULT_VISIBILITY_SCOPE,
        collection_object_id=payload.collection_object_id,
        profile_key=sheet.image_type,
        management={**_sheet_management_defaults(sheet), **_normalize_json_dict(payload.management)},
        profile_fields=_normalize_json_dict(payload.profile_fields),
        raw_metadata={**_normalize_json_dict(payload.raw_metadata), "sheet_id": sheet.id, "line_no": record.line_no},
        assigned_photographer_user_id=sheet.assigned_photographer_user_id,
    )
    _apply_record_payload(record, merged_payload, db, user)
    sheet.status = _sheet_status(sheet)
    db.commit()
    db.refresh(record)
    return _serialize_image_record_detail(record, db)


@router.patch("/sheets/items/{record_id}", response_model=ImageRecordDetailResponse)
def update_image_ingest_sheet_item(
    record_id: int,
    payload: ImageRecordSaveRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.edit")),
):
    record = _get_image_record_or_404(record_id, db)
    if record.sheet_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image record is not attached to an ingest sheet")
    sheet = _get_sheet_or_404(record.sheet_id, db)
    merged_payload = ImageRecordSaveRequest(
        record_no=payload.record_no,
        title=payload.title,
        resource_type=payload.resource_type or record.resource_type,
        visibility_scope=payload.visibility_scope or record.visibility_scope,
        collection_object_id=payload.collection_object_id,
        profile_key=sheet.image_type,
        management={**_sheet_management_defaults(sheet), **_normalize_json_dict(payload.management)},
        profile_fields=_normalize_json_dict(payload.profile_fields),
        raw_metadata={**_normalize_json_dict(payload.raw_metadata), "sheet_id": sheet.id, "line_no": record.line_no},
        assigned_photographer_user_id=sheet.assigned_photographer_user_id,
    )
    _apply_record_payload(record, merged_payload, db, user)
    sheet.status = _sheet_status(sheet)
    db.commit()
    db.refresh(record)
    return _serialize_image_record_detail(record, db)


@router.post("", response_model=ImageRecordDetailResponse, status_code=status.HTTP_201_CREATED)
def create_image_record(
    payload: ImageRecordSaveRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.create")),
):
    record = ImageRecord(
        record_no="PENDING",
        title=None,
        status=DRAFT_STATUS,
        resource_type=DEFAULT_RESOURCE_TYPE,
        visibility_scope=DEFAULT_VISIBILITY_SCOPE,
        collection_object_id=None,
        profile_key=DEFAULT_PROFILE_KEY,
        metadata_info={},
        created_by_user_id=_normalize_optional_int(getattr(user, "user_id", None)),
    )

    creator = db.query(User).filter(User.username == user.user_id).first()
    if creator is not None:
        record.created_by_user_id = creator.id

    db.add(record)
    db.flush()

    if not _clean_optional_text(payload.record_no):
        record.record_no = f"IR-{datetime.now(timezone.utc):%Y%m%d}-{record.id:06d}"
    _apply_record_payload(record, payload, db, user)
    _append_audit_entry(record, "draft_created", user)

    db.commit()
    db.refresh(record)
    return _serialize_image_record_detail(record, db)


@router.get("", response_model=list[ImageRecordSummary])
def list_image_records(
    skip: int = 0,
    limit: int = 100,
    status_code: Annotated[str | None, Query(alias="status")] = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_any_permission("image.record.list", "image.record.view_ready_for_upload")),
):
    query = db.query(ImageRecord)

    normalized_status = _clean_optional_text(status_code)
    if normalized_status:
        query = query.filter(ImageRecord.status == normalized_status)
    elif not user.has_permission("image.record.list"):
        query = query.filter(ImageRecord.status.in_([READY_STATUS, UPLOADED_PENDING_VALIDATION_STATUS]))

    records = query.order_by(ImageRecord.updated_at.desc(), ImageRecord.id.desc()).all()
    normalized_q = _clean_optional_text(q)
    visible_records = [record for record in records if _is_visible_to_user(record, user) and _matches_query(record, normalized_q)]
    visible_records = visible_records[skip : skip + limit]
    return [_serialize_image_record(record) for record in visible_records]


@router.get("/{record_id}", response_model=ImageRecordDetailResponse)
def get_image_record(
    record_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.view")),
):
    record = _get_accessible_image_record(record_id, db, user)
    return _serialize_image_record_detail(record, db)


@router.patch("/{record_id}", response_model=ImageRecordDetailResponse)
def update_image_record(
    record_id: int,
    payload: ImageRecordSaveRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.edit")),
):
    record = _get_image_record_or_404(record_id, db)
    _apply_record_payload(record, payload, db, user)
    _append_audit_entry(record, "draft_updated", user)
    db.commit()
    db.refresh(record)
    return _serialize_image_record_detail(record, db)


@router.post("/{record_id}/submit", response_model=ImageRecordDetailResponse)
def submit_image_record(
    record_id: int,
    payload: ImageRecordActionRequest | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.submit")),
):
    record = _get_image_record_or_404(record_id, db)
    validation = _validation_state(record, db)
    if not validation.ready_for_submit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Image record is missing required fields for ready-for-upload",
                "missing_fields": validation.missing_fields,
                "missing_labels": validation.missing_labels,
                "validation": validation.model_dump(),
            },
        )

    submitter = _find_user_entity(db, user)
    _set_record_status(record, READY_STATUS)
    record.submitted_by_user_id = submitter.id if submitter is not None else record.submitted_by_user_id
    record.submitted_at = datetime.now(timezone.utc)
    layers = dict(_record_layers(record))
    management = layers.get("management")
    if not isinstance(management, dict):
        management = {}
    else:
        management = dict(management)
    management["image_record_time"] = record.submitted_at.isoformat()
    layers["management"] = management
    record.metadata_info = layers

    _append_audit_entry(record, "submitted", user, payload.note if payload else None)
    db.commit()
    db.refresh(record)
    return _serialize_image_record_detail(record, db)


@router.post("/{record_id}/return", response_model=ImageRecordDetailResponse)
def return_image_record(
    record_id: int,
    payload: ImageRecordActionRequest | None = None,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.record.return")),
):
    record = _get_image_record_or_404(record_id, db)
    if record.status != READY_STATUS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only ready-for-upload records can be returned")

    _clear_pending_upload(record)
    _set_record_status(record, RETURNED_STATUS)
    layers = dict(_record_layers(record))
    management = layers.get("management")
    if not isinstance(management, dict):
        management = {}
    else:
        management = dict(management)
    if payload and payload.note:
        management["return_note"] = payload.note
    management["returned_at"] = datetime.now(timezone.utc).isoformat()
    layers["management"] = management
    record.metadata_info = layers

    _append_audit_entry(record, "returned", user, payload.note if payload else None)
    db.commit()
    db.refresh(record)
    return _serialize_image_record_detail(record, db)


@router.post("/{record_id}/upload-temp", response_model=ImageRecordDetailResponse)
async def upload_temp_image_for_record(
    record_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.file.upload")),
):
    record = _get_accessible_image_record(record_id, db, user)
    if record.status not in {READY_STATUS, UPLOADED_PENDING_VALIDATION_STATUS}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temporary upload is only allowed for records that are ready for upload or awaiting validation",
        )

    _clear_pending_upload(record)

    filename = os.path.basename(file.filename or "")
    if not filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload filename is required")

    temp_directory = _temp_upload_dir()
    temp_path = os.path.join(temp_directory, f"record-{record.id}-{secrets.token_hex(8)}-{filename}")
    file_size = await _write_upload_file(temp_path, file)

    pending_upload = _build_pending_upload_payload(record, file, temp_path, file_size, db, user)
    _set_pending_upload(record, pending_upload)
    _append_audit_entry(record, "temp_upload_created", user, filename)

    db.commit()
    db.refresh(record)
    return _serialize_image_record_detail(record, db)


@router.post("/{record_id}/confirm-bind", response_model=ImageRecordDetailResponse)
def confirm_bind_image_record(
    record_id: int,
    payload: ImageRecordConfirmRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.file.match")),
):
    record = _get_accessible_image_record(record_id, db, user)
    if record.asset is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image record already has an active asset; use confirm-replace instead")

    pending_upload = _assert_confirm_token(record, payload)
    validation = _revalidate_pending_upload(record, pending_upload, db, user)
    if validation.has_blocking_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Pending upload has blocking validation issues",
                "validation": validation.model_dump(),
            },
        )

    _enforce_unique_representative_image(record, db)

    db_asset = Asset(
        filename=str(pending_upload.get("filename") or ""),
        file_path=str(pending_upload.get("temp_path") or ""),
        file_size=int(pending_upload.get("file_size") or 0),
        mime_type=_clean_optional_text(pending_upload.get("mime_type")),
        visibility_scope=record.visibility_scope,
        collection_object_id=record.collection_object_id,
        image_record_id=record.id,
        status="processing",
        resource_type=record.resource_type,
        process_message="Bound to image record and awaiting validation",
        metadata_info=_build_asset_metadata_from_pending_upload(record, pending_upload, user),
    )
    _apply_asset_access_strategy(db_asset)
    db.add(db_asset)
    db.flush()

    _set_record_status(record, UPLOADED_PENDING_VALIDATION_STATUS)
    _set_binding_validation(record, validation)
    _set_face_recognition_pending(record, db_asset)
    _set_pending_upload(record, None)
    _append_audit_entry(record, "asset_bound", user, payload.note)

    db.commit()
    db.refresh(record)
    db.refresh(db_asset)
    _enqueue_asset_derivative_generation(db_asset)
    _enqueue_business_activity_face_recognition(record, db_asset)
    return _serialize_image_record_detail(record, db)


@router.post("/{record_id}/confirm-replace", response_model=ImageRecordDetailResponse)
def confirm_replace_image_record_asset(
    record_id: int,
    payload: ImageRecordConfirmRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.file.match")),
):
    record = _get_accessible_image_record(record_id, db, user)
    if record.asset is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image record does not have an active asset to replace")

    pending_upload = _assert_confirm_token(record, payload)
    validation = _revalidate_pending_upload(record, pending_upload, db, user)
    if validation.has_blocking_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Pending upload has blocking validation issues",
                "validation": validation.model_dump(),
            },
        )

    _enforce_unique_representative_image(record, db)

    replaced_asset = _replace_current_asset_binding(record, user, payload.note)
    db.flush()

    db_asset = Asset(
        filename=str(pending_upload.get("filename") or ""),
        file_path=str(pending_upload.get("temp_path") or ""),
        file_size=int(pending_upload.get("file_size") or 0),
        mime_type=_clean_optional_text(pending_upload.get("mime_type")),
        visibility_scope=record.visibility_scope,
        collection_object_id=record.collection_object_id,
        image_record_id=record.id,
        status="processing",
        resource_type=record.resource_type,
        process_message="Replacement bound to image record and awaiting validation",
        metadata_info=_build_asset_metadata_from_pending_upload(record, pending_upload, user),
    )
    _apply_asset_access_strategy(db_asset)
    db.add(db_asset)
    db.flush()

    _set_record_status(record, UPLOADED_PENDING_VALIDATION_STATUS)
    _set_binding_validation(record, validation)
    _set_face_recognition_pending(record, db_asset)
    _set_pending_upload(record, None)
    _append_audit_entry(record, "asset_replaced", user, payload.note or f"replaced_asset_id={replaced_asset.id}")

    db.commit()
    db.refresh(record)
    db.refresh(db_asset)
    _enqueue_asset_derivative_generation(db_asset)
    _enqueue_business_activity_face_recognition(record, db_asset)
    return _serialize_image_record_detail(record, db)
