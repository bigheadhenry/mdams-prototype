from __future__ import annotations

from typing import Any

from ..models import Asset, ImageRecord
from ..permissions import CurrentUser
from ..schemas import ImageRecordValidationResult, ImageRecordValidationRule, ImageRecordValidationState
from .cultural_object_lookup import TEMPORARY_OBJECT_NUMBER_TOKENS
from .metadata_layers import PROFILE_DEFINITIONS, get_fixity_sha256

VALIDATION_STATUS_NOT_RUN = "not_run"
VALIDATION_STATUS_PASSED = "passed"
VALIDATION_STATUS_WARNING = "warning"
VALIDATION_STATUS_FAILED = "failed"

VALIDATION_LEVEL_ERROR = "error"
VALIDATION_LEVEL_WARNING = "warning"
VALIDATION_LEVEL_INFO = "info"

ALLOWED_UPLOAD_EXTENSIONS = {"jpg", "jpeg", "png", "tif", "tiff", "psd", "psb"}
ALLOWED_VISIBILITY_SCOPES = {"open", "owner_only"}
ALLOWED_SUBMIT_STATUSES = {"draft", "returned"}
ALLOWED_UPLOAD_STATUSES = {"ready_for_upload", "uploaded_pending_validation"}
UNUSUALLY_LARGE_FILE_SIZE = 200 * 1024 * 1024

FIELD_LABELS: dict[str, str] = {
    "record_no": "Record No",
    "title": "Title",
    "visibility_scope": "Visibility Scope",
    "profile_key": "Profile",
    "project_name": "Project Name",
    "image_category": "Image Category",
    "assigned_photographer_user_id": "Assigned Photographer",
    "main_location": "Main Location",
    "object_name": "Object Name",
    "building_name": "Building Name",
    "archive_number": "Archive Number",
}

PROFILE_REQUIRED_FIELDS: dict[str, list[str]] = {
    "business_activity": ["main_location"],
    "movable_artifact": ["object_number"],
    "immovable_artifact": ["building_name"],
    "ancient_tree": ["archive_number"],
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


def _field_label(field_key: str) -> str:
    return FIELD_LABELS.get(field_key) or field_key.replace("_", " ").title()


def _make_rule(
    *,
    code: str,
    level: str,
    message: str,
    field: str | None = None,
) -> ImageRecordValidationRule:
    return ImageRecordValidationRule(
        code=code,
        level=level,
        field=field,
        message=message,
        blocking=level == VALIDATION_LEVEL_ERROR,
        requires_confirmation=level == VALIDATION_LEVEL_WARNING,
    )


def _build_validation_result(rules: list[ImageRecordValidationRule]) -> ImageRecordValidationResult:
    blocking_count = sum(1 for rule in rules if rule.blocking)
    warning_count = sum(1 for rule in rules if rule.requires_confirmation)
    info_count = sum(1 for rule in rules if rule.level == VALIDATION_LEVEL_INFO)

    if blocking_count:
        validation_status = VALIDATION_STATUS_FAILED
    elif warning_count:
        validation_status = VALIDATION_STATUS_WARNING
    else:
        validation_status = VALIDATION_STATUS_PASSED

    parts: list[str] = []
    if blocking_count:
        parts.append(f"{blocking_count} blocking")
    if warning_count:
        parts.append(f"{warning_count} warning")
    if info_count:
        parts.append(f"{info_count} hint")

    summary = ", ".join(parts) if parts else "Validation passed"
    return ImageRecordValidationResult(
        validation_status=validation_status,
        validation_summary=summary,
        validation_report=rules,
        has_blocking_errors=blocking_count > 0,
        has_warnings=warning_count > 0,
        requires_confirmation=warning_count > 0,
    )


def _looks_placeholder_title(title: str | None) -> bool:
    if not title:
        return False
    normalized = title.strip().lower()
    placeholder_tokens = {"test", "todo", "temp", "placeholder", "untitled", "image", "photo"}
    if normalized in placeholder_tokens:
        return True
    return len(normalized) < 4


def _tags_missing(value: object | None) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return not any(_clean_optional_text(item) for item in value)
    return _clean_optional_text(value) is None


def _is_hex_sha256(value: str | None) -> bool:
    if value is None or len(value) != 64:
        return False
    return all(character in "0123456789abcdef" for character in value.lower())


def _is_temporary_object_number(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {token.lower() for token in TEMPORARY_OBJECT_NUMBER_TOKENS}


def _is_effective_duplicate(asset: Asset) -> bool:
    return (asset.status or "").lower() != "superseded"


def validate_image_record_for_submit(record: ImageRecord, *, record_no_is_unique: bool) -> ImageRecordValidationState:
    rules: list[ImageRecordValidationRule] = []
    management = _management_section(record)
    profile_fields = _profile_fields(record)

    record_no = _clean_optional_text(record.record_no)
    title = _clean_optional_text(record.title)
    visibility_scope = _clean_optional_text(record.visibility_scope)
    profile_key = _clean_optional_text(record.profile_key)
    project_name = _clean_optional_text(management.get("project_name"))
    image_category = _clean_optional_text(management.get("image_category"))
    assigned_photographer_user_id = _normalize_optional_int(record.assigned_photographer_user_id)

    if record.status not in ALLOWED_SUBMIT_STATUSES:
        rules.append(
            _make_rule(
                code="submit.invalid_status",
                level=VALIDATION_LEVEL_ERROR,
                field="status",
                message=f"Current status {record.status!r} does not allow submission",
            )
        )
    if not record_no:
        rules.append(
            _make_rule(
                code="submit.record_no.missing",
                level=VALIDATION_LEVEL_ERROR,
                field="record_no",
                message="Record No is required",
            )
        )
    elif not record_no_is_unique:
        rules.append(
            _make_rule(
                code="submit.record_no.duplicate",
                level=VALIDATION_LEVEL_ERROR,
                field="record_no",
                message="Record No must be unique",
            )
        )
    if not title:
        rules.append(
            _make_rule(
                code="submit.title.missing",
                level=VALIDATION_LEVEL_ERROR,
                field="title",
                message="Title is required",
            )
        )
    if not visibility_scope or visibility_scope.lower() not in ALLOWED_VISIBILITY_SCOPES:
        rules.append(
            _make_rule(
                code="submit.visibility_scope.invalid",
                level=VALIDATION_LEVEL_ERROR,
                field="visibility_scope",
                message="Visibility scope is missing or invalid",
            )
        )
    if not profile_key or profile_key not in PROFILE_DEFINITIONS:
        rules.append(
            _make_rule(
                code="submit.profile_key.invalid",
                level=VALIDATION_LEVEL_ERROR,
                field="profile_key",
                message="Profile is missing or invalid",
            )
        )
    if not project_name:
        rules.append(
            _make_rule(
                code="submit.project_name.missing",
                level=VALIDATION_LEVEL_ERROR,
                field="project_name",
                message="Project Name is required",
            )
        )
    if not image_category:
        rules.append(
            _make_rule(
                code="submit.image_category.missing",
                level=VALIDATION_LEVEL_ERROR,
                field="image_category",
                message="Image Category is required",
            )
        )
    if assigned_photographer_user_id is None:
        rules.append(
            _make_rule(
                code="submit.assigned_photographer.missing",
                level=VALIDATION_LEVEL_ERROR,
                field="assigned_photographer_user_id",
                message="Assigned photographer is required",
            )
        )

    for field_key in PROFILE_REQUIRED_FIELDS.get(record.profile_key, []):
        if not _clean_optional_text(profile_fields.get(field_key)):
            rules.append(
                _make_rule(
                    code=f"submit.profile.{field_key}.missing",
                    level=VALIDATION_LEVEL_ERROR,
                    field=field_key,
                    message=f"{_field_label(field_key)} is required for the selected profile",
                )
            )

    object_number = _clean_optional_text(profile_fields.get("object_number"))
    object_name = _clean_optional_text(profile_fields.get("object_name"))

    if not _clean_optional_text(profile_fields.get("object_number")):
        rules.append(
            _make_rule(
                code="submit.object_number.missing",
                level=VALIDATION_LEVEL_WARNING,
                field="object_number",
                message="Object Number is still missing",
            )
        )
    if record.profile_key == "movable_artifact" and not _is_temporary_object_number(object_number) and not object_name:
        rules.append(
            _make_rule(
                code="submit.object_name.missing",
                level=VALIDATION_LEVEL_WARNING,
                field="object_name",
                message="Object Name has not been filled from the cultural object lookup yet",
            )
        )
    if not _clean_optional_text(management.get("capture_time")):
        rules.append(
            _make_rule(
                code="submit.capture_time.missing",
                level=VALIDATION_LEVEL_WARNING,
                field="capture_time",
                message="Capture Time is missing",
            )
        )
    if not _clean_optional_text(management.get("photographer")):
        rules.append(
            _make_rule(
                code="submit.photographer.missing",
                level=VALIDATION_LEVEL_WARNING,
                field="photographer",
                message="Photographer is missing",
            )
        )
    if not _clean_optional_text(management.get("copyright_owner")):
        rules.append(
            _make_rule(
                code="submit.copyright_owner.missing",
                level=VALIDATION_LEVEL_WARNING,
                field="copyright_owner",
                message="Copyright Owner is missing",
            )
        )
    if _looks_placeholder_title(title):
        rules.append(
            _make_rule(
                code="submit.title.placeholder",
                level=VALIDATION_LEVEL_WARNING,
                field="title",
                message="Title looks too short or placeholder-like",
            )
        )

    if _tags_missing(management.get("tags")):
        rules.append(
            _make_rule(
                code="submit.tags.missing",
                level=VALIDATION_LEVEL_INFO,
                field="tags",
                message="Tags have not been filled in yet",
            )
        )
    if not _clean_optional_text(management.get("record_account")):
        rules.append(
            _make_rule(
                code="submit.record_account.missing",
                level=VALIDATION_LEVEL_INFO,
                field="record_account",
                message="Record Account is missing",
            )
        )
    if not _clean_optional_text(management.get("image_record_time")):
        rules.append(
            _make_rule(
                code="submit.image_record_time.missing",
                level=VALIDATION_LEVEL_INFO,
                field="image_record_time",
                message="Image Record Time has not been generated yet",
            )
        )

    result = _build_validation_result(rules)
    missing_fields = [rule.field for rule in rules if rule.blocking and rule.field]
    missing_labels = [_field_label(field_key) for field_key in missing_fields]

    return ImageRecordValidationState(
        ready_for_submit=not result.has_blocking_errors,
        missing_fields=missing_fields,
        missing_labels=missing_labels,
        validation_status=result.validation_status,
        validation_summary=result.validation_summary,
        validation_report=result.validation_report,
        has_blocking_errors=result.has_blocking_errors,
        has_warnings=result.has_warnings,
        requires_confirmation=result.requires_confirmation,
    )


def validate_bound_image_record(
    record: ImageRecord,
    pending_upload: dict[str, Any],
    duplicate_assets: list[Asset],
    actor: CurrentUser,
) -> ImageRecordValidationResult:
    rules: list[ImageRecordValidationRule] = []
    profile_fields = _profile_fields(record)
    original_filename = _clean_optional_text(pending_upload.get("filename")) or "uploaded file"
    lowered_filename = original_filename.lower()
    extension = (_clean_optional_text(pending_upload.get("extension")) or "").lower()
    file_size = _normalize_optional_int(pending_upload.get("file_size")) or 0
    width = _normalize_optional_int(pending_upload.get("width"))
    height = _normalize_optional_int(pending_upload.get("height"))
    frame_count = _normalize_optional_int(pending_upload.get("frame_count")) or 1
    sha256 = _clean_optional_text(pending_upload.get("sha256"))
    assigned_username = getattr(record.assigned_photographer_user, "username", None)
    replacement_mode = record.asset is not None

    if not actor.has_permission("system.manage") and assigned_username != actor.user_id:
        rules.append(
            _make_rule(
                code="bind.assigned_photographer.mismatch",
                level=VALIDATION_LEVEL_ERROR,
                field="assigned_photographer_user_id",
                message="Current user is not the assigned photographer for this record",
            )
        )

    if record.status not in ALLOWED_UPLOAD_STATUSES:
        rules.append(
            _make_rule(
                code="bind.invalid_status",
                level=VALIDATION_LEVEL_ERROR,
                field="status",
                message=f"Current status {record.status!r} does not allow upload binding",
            )
        )

    if file_size <= 0:
        rules.append(
            _make_rule(
                code="bind.file.empty",
                level=VALIDATION_LEVEL_ERROR,
                field="file_size",
                message="Uploaded file is empty",
            )
        )

    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        rules.append(
            _make_rule(
                code="bind.file_type.invalid",
                level=VALIDATION_LEVEL_ERROR,
                field="extension",
                message=f"File type .{extension or 'unknown'} is not allowed",
            )
        )

    if not _is_hex_sha256(sha256):
        rules.append(
            _make_rule(
                code="bind.hash.invalid",
                level=VALIDATION_LEVEL_ERROR,
                field="sha256",
                message="SHA256 hash is missing or invalid",
            )
        )

    if width is None or height is None:
        rules.append(
            _make_rule(
                code="bind.dimensions.unavailable",
                level=VALIDATION_LEVEL_ERROR,
                field="dimensions",
                message="File is unreadable or image dimensions could not be extracted",
            )
        )

    current_asset = record.asset
    current_asset_hash = get_fixity_sha256(current_asset.metadata_info) if current_asset is not None else None
    if replacement_mode and current_asset_hash and sha256 and current_asset_hash == sha256:
        rules.append(
            _make_rule(
                code="replace.hash.identical",
                level=VALIDATION_LEVEL_ERROR,
                field="sha256",
                message="Replacement file is identical to the current effective image",
            )
        )

    duplicate_candidate = next(
        (
            asset
            for asset in duplicate_assets
            if (current_asset is None or asset.id != current_asset.id) and _is_effective_duplicate(asset)
        ),
        None,
    )
    if duplicate_candidate is not None:
        rules.append(
            _make_rule(
                code="bind.hash.duplicate",
                level=VALIDATION_LEVEL_ERROR,
                field="sha256",
                message="The same file hash already exists on another effective asset",
            )
        )

    if record.record_no.lower() not in lowered_filename:
        rules.append(
            _make_rule(
                code="bind.filename.record_no_missing",
                level=VALIDATION_LEVEL_WARNING,
                field="filename",
                message="Filename does not contain the record number",
            )
        )

    object_number = _clean_optional_text(profile_fields.get("object_number"))
    if object_number and object_number.lower() not in lowered_filename:
        rules.append(
            _make_rule(
                code="bind.filename.object_number_missing",
                level=VALIDATION_LEVEL_WARNING,
                field="filename",
                message="Filename does not contain the object number",
            )
        )

    if extension in {"psd", "psb"}:
        rules.append(
            _make_rule(
                code="bind.layer_risk.psd_family",
                level=VALIDATION_LEVEL_WARNING,
                field="extension",
                message="PSD or PSB upload may contain layer risk",
            )
        )

    if extension in {"tif", "tiff"} and frame_count > 1:
        rules.append(
            _make_rule(
                code="bind.layer_risk.tiff_multi_page",
                level=VALIDATION_LEVEL_WARNING,
                field="extension",
                message="TIFF appears to have multi-page risk",
            )
        )

    if file_size >= UNUSUALLY_LARGE_FILE_SIZE:
        rules.append(
            _make_rule(
                code="bind.file.large",
                level=VALIDATION_LEVEL_WARNING,
                field="file_size",
                message="File is unusually large and processing may be slow",
            )
        )

    if extension == "psb":
        rules.append(
            _make_rule(
                code="bind.psb.preview_conversion",
                level=VALIDATION_LEVEL_WARNING,
                field="extension",
                message="PSB requires background conversion before preview",
            )
        )

    if not original_filename.startswith(f"{record.record_no}-") and not original_filename.startswith(f"{record.record_no}_"):
        rules.append(
            _make_rule(
                code="bind.filename.naming_convention",
                level=VALIDATION_LEVEL_INFO,
                field="filename",
                message="Filename does not follow the recommended naming convention",
            )
        )

    if extension in {"jpg", "jpeg", "png"}:
        rules.append(
            _make_rule(
                code="bind.derivative.iiif_recommended",
                level=VALIDATION_LEVEL_INFO,
                field="derivative",
                message="IIIF access derivative generation is recommended",
            )
        )

    return _build_validation_result(rules)
