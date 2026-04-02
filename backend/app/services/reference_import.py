from __future__ import annotations

import hashlib
import json
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .metadata_layers import PROFILE_KEY_ALIASES

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".psb"}
REFERENCE_SOURCE_SYSTEM = "reference_resource_pack"
REFERENCE_SOURCE_LABEL = "Reference Resource Pack"
COMPLETENESS_FIELD_RULES = {
    "core": ("title", "source_system", "resource_type", "visibility_scope"),
    "management": ("project_name", "image_category", "image_name"),
    "technical": ("original_file_name", "file_size", "checksum", "ingest_method"),
}
PROFILE_COMPLETENESS_RULES = {
    "business_activity": ("main_location",),
    "ancient_tree": ("archive_number",),
    "immovable_artifact": ("building_name",),
    "movable_artifact": ("object_name",),
    "archaeology": ("archaeology_image_category",),
    "other": (),
}

REFERENCE_PROFILE_MAP = {
    **PROFILE_KEY_ALIASES,
    "archaeology": "archaeology",
    "other": "other",
}

CATEGORY_PROFILE_MAP = {
    "业务活动影像": "business_activity",
    "其他影像": "other",
    "古树影像": "ancient_tree",
    "文物建筑影像": "immovable_artifact",
    "文物影像": "movable_artifact",
    "考古影像": "archaeology",
}


@dataclass(frozen=True)
class ReferenceImportCandidate:
    source_dir: Path
    category_dir: Path
    primary_image: Path
    unified_json: Path | None
    source_json: Path | None
    profile_key: str
    title: str
    manifest: dict[str, Any]
    warnings: tuple[str, ...]
    quality_flags: tuple[str, ...]


MOJIBAKE_MARKERS = (
    "锟",
    "鈥",
    "鍗",
    "涓",
    "鏁",
    "闄",
    "诲",
    "缂",
    "妗",
    "鐗",
    "鍏",
    "绗",
)


def _load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _iter_candidate_dirs(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_dir())


def _is_screenshot(path: Path) -> bool:
    return path.name.lower().startswith("fireshot capture ")


def _iter_image_files(directory: Path) -> list[Path]:
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def select_primary_image(directory: Path) -> Path | None:
    image_files = _iter_image_files(directory)
    if not image_files:
        return None

    non_screenshots = [path for path in image_files if not _is_screenshot(path)]
    if non_screenshots:
        return sorted(non_screenshots, key=lambda path: (path.suffix.lower() not in {".tif", ".tiff"}, path.name))[0]
    return image_files[0]


def _find_sidecar(directory: Path, suffix: str) -> Path | None:
    matches = sorted(directory.glob(suffix))
    return matches[0] if matches else None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(64 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _mime_type(path: Path) -> str:
    guessed, _encoding = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def build_import_filename(primary_image: Path, relative_dir: Path) -> str:
    suffix = hashlib.sha1(str(relative_dir).encode("utf-8")).hexdigest()[:10]
    stem = primary_image.stem.replace(" ", "_")
    return f"{suffix}__{stem}{primary_image.suffix.lower()}"


def _contains_mojibake(value: Any) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in MOJIBAKE_MARKERS)
    if isinstance(value, dict):
        return any(_contains_mojibake(key) or _contains_mojibake(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_mojibake(item) for item in value)
    return False


def _normalize_profile_key(unified_data: dict[str, Any], category_name: str) -> str:
    candidate = str(unified_data.get("profile_key") or "").strip()
    if candidate:
        return REFERENCE_PROFILE_MAP.get(candidate, candidate if candidate else "other")
    return CATEGORY_PROFILE_MAP.get(category_name, "other")


def _extract_unified_layers(unified_data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    layers = unified_data.get("metadata_layers")
    if not isinstance(layers, dict):
        return {}, {}, {}, {}
    core = layers.get("core") if isinstance(layers.get("core"), dict) else {}
    technical = layers.get("technical") if isinstance(layers.get("technical"), dict) else {}
    modality = layers.get("modality") if isinstance(layers.get("modality"), dict) else {}
    source_record = layers.get("source_record") if isinstance(layers.get("source_record"), dict) else {}
    return core, technical, modality, source_record


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", []):
            return value
    return None


def _build_profile_fields(
    profile_key: str,
    source_dir: Path,
    title: str,
    source_label: str,
    modality: dict[str, Any] | None = None,
    source_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    modality = modality or {}
    source_record = source_record or {}
    if profile_key == "movable_artifact":
        return {"object_name": title}
    if profile_key == "immovable_artifact":
        return {"building_name": source_dir.name}
    if profile_key == "ancient_tree":
        return {"archive_number": source_dir.name}
    if profile_key == "archaeology":
        return {"archaeology_image_category": source_label}
    if profile_key == "business_activity":
        main_location = _first_present(
            modality.get("主题地点"),
            source_record.get("主题地点"),
            modality.get("主要地点"),
            source_record.get("主要地点"),
        )
        main_person = _first_present(
            modality.get("主要人物"),
            source_record.get("主要人物"),
        )
        fields: dict[str, Any] = {}
        if main_location not in (None, "", []):
            fields["main_location"] = main_location
        if main_person not in (None, "", []):
            fields["main_person"] = main_person
        return fields
    return {}


def build_reference_manifest(
    *,
    source_dir: Path,
    source_root: Path,
    visibility_scope: str = "open",
) -> ReferenceImportCandidate | None:
    primary_image = select_primary_image(source_dir)
    if primary_image is None:
        return None

    unified_json = _find_sidecar(source_dir, "*.unified.json")
    source_json_candidates = sorted(
        path for path in source_dir.glob("*.json") if not path.name.endswith(".unified.json")
    )
    source_json = source_json_candidates[0] if source_json_candidates else None

    unified_data = _load_json(unified_json)
    source_data = _load_json(source_json)
    core, technical, modality, source_record = _extract_unified_layers(unified_data)

    category_dir = source_dir.parent
    category_name = category_dir.name if category_dir != source_root else source_dir.name
    profile_key = _normalize_profile_key(unified_data, category_name)
    checksum = _sha256(primary_image)
    title = str(unified_data.get("title") or core.get("title") or source_dir.name)
    source_label = str(unified_data.get("source_label") or category_name)
    updated_at = unified_data.get("updated_at") or core.get("recorded_at")
    relative_dir = source_dir.relative_to(source_root)

    management = {
        "project_type": source_label,
        "project_name": source_dir.name,
        "photographer": (unified_data.get("creators") or [core.get("creator")] or [None])[0],
        "photographer_org": core.get("creator_org"),
        "copyright_owner": unified_data.get("rights") or core.get("rights"),
        "capture_time": core.get("capture_date") or updated_at,
        "image_category": source_label,
        "image_name": title,
        "capture_content": core.get("content") or unified_data.get("summary"),
        "representative_image": core.get("is_representative"),
        "remark": unified_data.get("summary"),
        "tags": unified_data.get("keywords") or [],
        "record_account": core.get("recorded_by"),
        "record_time": core.get("recorded_at") or updated_at,
        "image_record_time": source_record.get("影像录入时间") or updated_at,
    }

    manifest_metadata = {
        "core": {
            "source_system": REFERENCE_SOURCE_SYSTEM,
            "source_label": REFERENCE_SOURCE_LABEL,
            "resource_type": "image_2d_cultural_object",
            "title": title,
            "status": "ready",
            "visibility_scope": visibility_scope,
        },
        "management": {key: value for key, value in management.items() if value not in (None, "", [])},
        "technical": {
            "original_file_name": primary_image.name,
            "image_file_name": primary_image.name,
            "identifier_type": "reference_source_id",
            "identifier_value": unified_data.get("source_id"),
            "file_size": primary_image.stat().st_size,
            "format_name": primary_image.suffix.lower().lstrip("."),
            "checksum_algorithm": "SHA256",
            "checksum": checksum,
            "fixity_sha256": checksum,
            "ingest_method": "reference_manifest",
            "original_file_path": str(primary_image),
            "original_mime_type": _mime_type(primary_image),
            "source_json_file": source_json.name if source_json else None,
            "source_unified_json_file": unified_json.name if unified_json else None,
        },
        "profile": {
            "key": profile_key,
            "fields": _build_profile_fields(profile_key, source_dir, title, source_label, modality, source_record),
        },
        "raw_metadata": {
            "reference_category": category_name,
            "reference_relative_dir": str(relative_dir),
            "reference_primary_image": str(primary_image),
            "reference_unified_json": unified_data,
            "reference_source_json": source_data,
            "reference_modality": modality,
            "reference_source_record": source_record,
        },
    }

    warnings: list[str] = []
    if _is_screenshot(primary_image):
        warnings.append("primary image fell back to screenshot because no non-screenshot image was found")
    if unified_json is None:
        warnings.append("missing unified sidecar")
    if source_json is None:
        warnings.append("missing source json sidecar")

    quality_flags: list[str] = []
    if _contains_mojibake(unified_data):
        quality_flags.append("unified sidecar contains mojibake")
    if _contains_mojibake(source_data):
        quality_flags.append("source sidecar contains mojibake")
    if _contains_mojibake(title):
        quality_flags.append("title contains mojibake")
    if unified_json is None:
        quality_flags.append("missing unified sidecar")
    if source_json is None:
        quality_flags.append("missing source json sidecar")
    if _is_screenshot(primary_image):
        quality_flags.append("no non-screenshot primary image found")

    manifest = {
        "hash": checksum,
        "metadata": manifest_metadata,
    }

    return ReferenceImportCandidate(
        source_dir=source_dir,
        category_dir=category_dir,
        primary_image=primary_image,
        unified_json=unified_json,
        source_json=source_json,
        profile_key=profile_key,
        title=title,
        manifest=manifest,
        warnings=tuple(warnings),
        quality_flags=tuple(quality_flags),
    )


def collect_reference_candidates(
    source_root: Path,
    *,
    visibility_scope: str = "open",
    limit: int | None = None,
) -> list[ReferenceImportCandidate]:
    candidates: list[ReferenceImportCandidate] = []
    for directory in _iter_candidate_dirs(source_root):
        candidate = build_reference_manifest(
            source_dir=directory,
            source_root=source_root,
            visibility_scope=visibility_scope,
        )
        if candidate is None:
            continue
        candidates.append(candidate)
        if limit is not None and limit > 0 and len(candidates) >= limit:
            break
    return candidates


def assess_manifest_completeness(manifest: dict[str, Any]) -> dict[str, Any]:
    metadata = manifest.get("metadata") if isinstance(manifest, dict) else {}
    if not isinstance(metadata, dict):
        metadata = {}

    core = metadata.get("core") if isinstance(metadata.get("core"), dict) else {}
    management = metadata.get("management") if isinstance(metadata.get("management"), dict) else {}
    technical = metadata.get("technical") if isinstance(metadata.get("technical"), dict) else {}
    profile = metadata.get("profile") if isinstance(metadata.get("profile"), dict) else {}
    profile_fields = profile.get("fields") if isinstance(profile.get("fields"), dict) else {}
    profile_key = str(profile.get("key") or "other")

    missing: list[str] = []
    filled = 0
    expected = 0

    for section_name, fields in COMPLETENESS_FIELD_RULES.items():
        section = {"core": core, "management": management, "technical": technical}[section_name]
        for field in fields:
            expected += 1
            if section.get(field) not in (None, "", []):
                filled += 1
            else:
                missing.append(f"{section_name}.{field}")

    for field in PROFILE_COMPLETENESS_RULES.get(profile_key, ()):
        expected += 1
        if profile_fields.get(field) not in (None, "", []):
            filled += 1
        else:
            missing.append(f"profile.{field}")

    ratio = 1.0 if expected == 0 else round(filled / expected, 3)
    return {
        "profile_key": profile_key,
        "filled": filled,
        "expected": expected,
        "ratio": ratio,
        "missing": missing,
    }
