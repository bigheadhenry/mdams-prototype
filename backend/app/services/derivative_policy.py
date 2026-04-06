from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

TIFF_MIME_TYPES = {
    "image/tiff",
    "image/x-tiff",
    "image/tif",
}

JPEG_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/pjpeg",
    "image/jfif",
}

TIFF_EXTENSIONS = {".tif", ".tiff"}
PSB_EXTENSIONS = {".psb"}
JPEG_EXTENSIONS = {".jpg", ".jpeg", ".jpe", ".jfif"}

TIFF_SIZE_THRESHOLD_BYTES = 50 * 1024 * 1024
TIFF_PIXEL_THRESHOLD = 25_000_000
JPEG_SIZE_THRESHOLD_BYTES = 120 * 1024 * 1024
JPEG_PIXEL_THRESHOLD = 60_000_000


def _coerce_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_mime_type(mime_type: str | None) -> str:
    if not mime_type:
        return ""
    return str(mime_type).split(";", 1)[0].strip().lower()


def _source_family(*, filename: str | None, mime_type: str | None) -> str:
    normalized_mime_type = _normalize_mime_type(mime_type)
    suffix = Path(filename).suffix.lower() if filename else ""

    if suffix in PSB_EXTENSIONS:
        return "psb"
    if normalized_mime_type in TIFF_MIME_TYPES or suffix in TIFF_EXTENSIONS:
        return "tiff"
    if normalized_mime_type in JPEG_MIME_TYPES or suffix in JPEG_EXTENSIONS:
        return "jpeg"
    return "other"


def _pick_rule_id(source_family: str, file_size: int, pixel_count: int) -> str:
    if source_family == "psb":
        return "psb_mandatory_access_bigtiff"

    if source_family == "tiff":
        if file_size >= TIFF_SIZE_THRESHOLD_BYTES or pixel_count >= TIFF_PIXEL_THRESHOLD:
            return "tiff_large_pyramidal_tiled_copy"
        return "tiff_keep_original"

    if source_family == "jpeg":
        if file_size >= JPEG_SIZE_THRESHOLD_BYTES or pixel_count >= JPEG_PIXEL_THRESHOLD:
            return "jpeg_large_access_copy"
        return "jpeg_keep_original"

    return "keep_original"


def build_derivative_policy(
    *,
    filename: str | None,
    mime_type: str | None,
    file_size: int | None,
    width: int | None = None,
    height: int | None = None,
) -> dict[str, Any]:
    normalized_file_size = max(_coerce_int(file_size), 0)
    normalized_width = max(_coerce_int(width), 0)
    normalized_height = max(_coerce_int(height), 0)
    pixel_count = normalized_width * normalized_height if normalized_width and normalized_height else 0
    source_family = _source_family(filename=filename, mime_type=mime_type)
    rule_id = _pick_rule_id(source_family, normalized_file_size, pixel_count)

    if rule_id == "tiff_large_pyramidal_tiled_copy":
        return {
            "derivative_rule_id": rule_id,
            "derivative_strategy": "generate_pyramidal_tiff",
            "derivative_priority": "required",
            "derivative_target_format": "image/tiff",
            "derivative_source_family": source_family,
            "derivative_reason": (
                "Large TIFF/PSB assets benefit from a pyramidal tiled TIFF access copy for IIIF delivery."
            ),
            "derivative_threshold_bytes": TIFF_SIZE_THRESHOLD_BYTES,
            "derivative_threshold_pixels": TIFF_PIXEL_THRESHOLD,
        }

    if rule_id == "psb_mandatory_access_bigtiff":
        return {
            "derivative_rule_id": rule_id,
            "derivative_strategy": "generate_pyramidal_tiff",
            "derivative_priority": "required",
            "derivative_target_format": "image/tiff",
            "derivative_source_family": source_family,
            "derivative_reason": (
                "PSB assets require a pyramidal BigTIFF access copy for stable IIIF delivery."
            ),
            "derivative_threshold_bytes": None,
            "derivative_threshold_pixels": None,
        }

    if rule_id == "jpeg_large_access_copy":
        return {
            "derivative_rule_id": rule_id,
            "derivative_strategy": "generate_access_jpeg",
            "derivative_priority": "optional",
            "derivative_target_format": "image/jpeg",
            "derivative_source_family": source_family,
            "derivative_reason": (
                "Exceptionally large JPEG assets can use a lighter access copy, but do not need a pyramidal TIFF."
            ),
            "derivative_threshold_bytes": JPEG_SIZE_THRESHOLD_BYTES,
            "derivative_threshold_pixels": JPEG_PIXEL_THRESHOLD,
        }

    normalized_mime_type = _normalize_mime_type(mime_type) or "application/octet-stream"
    return {
        "derivative_rule_id": rule_id,
        "derivative_strategy": "keep_original",
        "derivative_priority": "none",
        "derivative_target_format": normalized_mime_type,
        "derivative_source_family": source_family,
        "derivative_reason": (
            "Keep the original file for display; no pyramidal TIFF conversion is recommended by default."
        ),
        "derivative_threshold_bytes": None,
        "derivative_threshold_pixels": None,
    }


def infer_derivative_policy_from_metadata(metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    source = dict(metadata) if isinstance(metadata, Mapping) else {}
    technical = source.get("technical") if isinstance(source.get("technical"), Mapping) else {}
    core = source.get("core") if isinstance(source.get("core"), Mapping) else {}

    filename = (
        technical.get("image_file_name")
        or technical.get("original_file_name")
        or source.get("image_file_name")
        or source.get("original_file_name")
        or core.get("title")
    )
    mime_type = technical.get("format_name") or technical.get("original_mime_type") or source.get("mime_type")
    file_size = technical.get("file_size") or source.get("file_size")
    width = technical.get("width") or source.get("width")
    height = technical.get("height") or source.get("height")

    return build_derivative_policy(
        filename=str(filename) if filename not in (None, "") else None,
        mime_type=str(mime_type) if mime_type not in (None, "") else None,
        file_size=_coerce_int(file_size),
        width=_coerce_int(width),
        height=_coerce_int(height),
    )
