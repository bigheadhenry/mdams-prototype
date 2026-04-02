from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping

from .derivative_policy import infer_derivative_policy_from_metadata

METADATA_SCHEMA_VERSION = "2.0"
SOURCE_SYSTEM = "mdams_2d_image_subsystem"
SOURCE_LABEL = "2D Image Subsystem"

PROFILE_KEY_ALIASES = {
    "activity": "business_activity",
    "tree": "ancient_tree",
    "building": "immovable_artifact",
    "cultural_object": "movable_artifact",
}

RESOURCE_TYPE_LABELS = {
    "image_2d_cultural_object": "2D Cultural Object Image",
}

SECTION_KEYS = {"core", "management", "technical", "raw_metadata"}
CORE_FIELD_LABELS = {
    "visibility_scope": "Visibility Scope",
    "collection_object_id": "Collection Object ID",
}

MANAGEMENT_FIELDS: list[tuple[str, str, tuple[str, ...]]] = [
    ("project_type", "Project Type", ("project_type", "项目类型")),
    ("project_name", "Project Name", ("project_name", "项目名称")),
    ("photographer", "Photographer", ("photographer", "摄影者")),
    ("photographer_org", "Photographer Org", ("photographer_org", "摄影者单位")),
    ("copyright_owner", "Copyright Owner", ("copyright_owner", "版权所属")),
    ("capture_time", "Capture Time", ("capture_time", "拍摄时间", "拍摄/制作时间")),
    ("image_category", "Image Category", ("image_category", "影像类别")),
    ("image_name", "Image Name", ("image_name", "影像名称")),
    ("capture_content", "Capture Content", ("capture_content", "拍摄内容", "拍摄/制作内容")),
    ("representative_image", "Representative Image", ("representative_image", "是否为代表影像")),
    ("remark", "Remark", ("remark", "备注")),
    ("tags", "Tags", ("tags", "影像标签")),
    ("record_account", "Record Account", ("record_account", "属性录入人员")),
    ("record_time", "Record Time", ("record_time", "属性录入时间")),
    ("image_record_time", "Image Record Time", ("image_record_time", "影像录入时间")),
]

TECHNICAL_FIELDS: list[tuple[str, str, tuple[str, ...]]] = [
    ("original_file_name", "Original File Name", ("original_file_name", "original_filename")),
    ("image_file_name", "Image File Name", ("image_file_name",)),
    ("iiif_access_file_name", "IIIF Access File Name", ("iiif_access_file_name",)),
    ("iiif_access_file_path", "IIIF Access File Path", ("iiif_access_file_path",)),
    ("iiif_access_mime_type", "IIIF Access MIME Type", ("iiif_access_mime_type",)),
    ("preview_image_name", "Preview Image Name", ("preview_image_name",)),
    ("preview_image_path", "Preview Image Path", ("preview_image_path",)),
    ("preview_image_mime_type", "Preview Image MIME Type", ("preview_image_mime_type",)),
    ("identifier_type", "Identifier Type", ("identifier_type",)),
    ("identifier_value", "Identifier Value", ("identifier_value",)),
    ("file_size", "File Size", ("file_size",)),
    ("format_name", "Format Name", ("format_name",)),
    ("format_version", "Format Version", ("format_version",)),
    ("registry_name", "Registry Name", ("registry_name",)),
    ("registry_item", "Registry Item", ("registry_item",)),
    ("byte_order", "Byte Order", ("byte_order",)),
    ("checksum_algorithm", "Checksum Algorithm", ("checksum_algorithm",)),
    ("checksum", "Checksum", ("checksum", "sha256", "SHA256")),
    ("checksum_generator", "Checksum Generator", ("checksum_generator",)),
    ("width", "Width", ("width",)),
    ("height", "Height", ("height",)),
    ("color_space", "Color Space", ("color_space",)),
    ("ingest_method", "Ingest Method", ("ingest_method",)),
    ("derivative_rule_id", "Derivative Rule ID", ("derivative_rule_id",)),
    ("derivative_strategy", "Derivative Strategy", ("derivative_strategy",)),
    ("derivative_priority", "Derivative Priority", ("derivative_priority",)),
    ("derivative_target_format", "Derivative Target Format", ("derivative_target_format",)),
    ("derivative_source_family", "Derivative Source Family", ("derivative_source_family",)),
    ("derivative_reason", "Derivative Reason", ("derivative_reason",)),
    ("derivative_threshold_bytes", "Derivative Threshold Bytes", ("derivative_threshold_bytes",)),
    ("derivative_threshold_pixels", "Derivative Threshold Pixels", ("derivative_threshold_pixels",)),
    ("fixity_sha256", "Fixity SHA256", ("fixity_sha256", "sha256", "SHA256")),
    ("conversion_method", "Conversion Method", ("conversion_method",)),
    ("original_file_path", "Original File Path", ("original_file_path",)),
    ("original_file_size", "Original File Size", ("original_file_size",)),
    ("original_mime_type", "Original MIME Type", ("original_mime_type",)),
    ("error_message", "Error Message", ("error_message",)),
]

PROFILE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "movable_artifact": {
        "label": "可移动文物",
        "sheet": "可移动文物",
        "aliases": ("movable_artifact", "image_2d_cultural_object", "cultural_object", "artifact"),
        "fields": [
            ("object_number", "Object Number", ("object_number", "文物号")),
            ("object_name", "Object Name", ("object_name", "文物名称")),
            ("object_level", "Object Level", ("object_level", "文物级别")),
            ("object_category", "Object Category", ("object_category", "文物类别")),
            ("object_subcategory", "Object Subcategory", ("object_subcategory", "文物细类")),
            ("management_group", "Management Group", ("management_group", "管理科组")),
            ("photographer", "Photographer", ("photographer", "摄影者")),
            ("photographer_phone", "Photographer Phone", ("photographer_phone", "摄影者电话")),
            ("visible_to_custodians_only", "Visible To Custodians Only", ("visible_to_custodians_only", "仅责任人可见")),
        ],
    },
    "immovable_artifact": {
        "label": "不可移动文物",
        "sheet": "不可移动文物",
        "aliases": ("immovable_artifact", "building"),
        "fields": [
            ("region_level_1", "Region Level 1", ("region_level_1", "一级区域")),
            ("region_level_2", "Region Level 2", ("region_level_2", "二级区域")),
            ("building_name", "Building Name", ("building_name", "文物建筑名称")),
            ("orientation", "Orientation", ("orientation", "方位")),
            ("part_level_1", "Part Level 1", ("part_level_1", "部位一级")),
            ("part_level_2", "Part Level 2", ("part_level_2", "部位二级")),
            ("part_level_3", "Part Level 3", ("part_level_3", "部位三级")),
            ("building_component", "Building Component", ("building_component", "建筑构件")),
        ],
    },
    "art_photography": {
        "label": "艺术摄影",
        "sheet": "艺术摄影",
        "aliases": ("art_photography",),
        "fields": [
            ("art_photography_type", "Art Photography Type", ("art_photography_type",)),
            ("collection_type", "Collection Type", ("collection_type",)),
            ("palace_area", "Palace Area", ("palace_area",)),
            ("season", "Season", ("season",)),
            ("plant", "Plant", ("plant",)),
            ("animal", "Animal", ("animal",)),
            ("solar_term", "Solar Term", ("solar_term",)),
            ("other", "Other", ("other",)),
            ("theme", "Theme", ("theme",)),
            ("cultural_topic", "Cultural Topic", ("cultural_topic",)),
            ("exhibition_topic", "Exhibition Topic", ("exhibition_topic",)),
        ],
    },
    "business_activity": {
        "label": "业务活动",
        "sheet": "业务活动",
        "aliases": ("business_activity", "activity"),
        "fields": [
            ("main_location", "Main Location", ("main_location", "主要地点")),
            ("main_person", "Main Person", ("main_person", "主要人物")),
        ],
    },
    "panorama": {
        "label": "全景",
        "sheet": "全景",
        "aliases": ("panorama",),
        "fields": [
            ("panorama_type", "Panorama Type", ("panorama_type",)),
            ("location", "Location", ("location",)),
        ],
    },
    "ancient_tree": {
        "label": "古树",
        "sheet": "古树",
        "aliases": ("ancient_tree", "tree"),
        "fields": [
            ("archive_number", "Archive Number", ("archive_number", "档案编号")),
            ("plant_type", "Plant Type", ("plant_type", "植物类型")),
            ("plant_name", "Plant Name", ("plant_name", "植物名称")),
            ("region", "Region", ("region", "所在区域")),
            ("specific_location", "Specific Location", ("specific_location", "具体位置")),
            ("grade", "Grade", ("grade", "等级")),
        ],
    },
    "archaeology": {
        "label": "考古",
        "sheet": "考古",
        "aliases": ("archaeology",),
        "fields": [
            ("archaeology_image_category", "Archaeology Image Category", ("archaeology_image_category", "考古影像分类")),
        ],
    },
    "other": {
        "label": "其他",
        "sheet": "其他",
        "aliases": ("other",),
        "fields": [],
    },
}

FIELD_LABELS: dict[str, str] = {}
for field_key, field_label, _aliases in MANAGEMENT_FIELDS + TECHNICAL_FIELDS:
    FIELD_LABELS[field_key] = field_label
for profile_definition in PROFILE_DEFINITIONS.values():
    for field_key, field_label, _aliases in profile_definition["fields"]:
        FIELD_LABELS[field_key] = field_label


def _as_dict(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return dict(value) if value else {}


def _is_layered_metadata(metadata: Mapping[str, Any] | None) -> bool:
    return bool(metadata) and any(key in metadata for key in SECTION_KEYS)


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _is_present(value: Any) -> bool:
    return value not in (None, "")


def _lookup_value(metadata: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in metadata and _is_present(metadata[key]):
            return metadata[key]

    nested = metadata.get("raw_metadata")
    if isinstance(nested, Mapping):
        for key in keys:
            if key in nested and _is_present(nested[key]):
                return nested[key]

    profile_block = metadata.get("profile")
    if isinstance(profile_block, Mapping):
        fields = profile_block.get("fields")
        if isinstance(fields, Mapping):
            for key in keys:
                if key in fields and _is_present(fields[key]):
                    return fields[key]

    for section_key in ("management", "technical"):
        section = metadata.get(section_key)
        if isinstance(section, Mapping):
            for key in keys:
                if key in section and _is_present(section[key]):
                    return section[key]

    return None


def _canonicalize_profile_key(candidate: Any) -> str | None:
    if candidate is None:
        return None
    candidate_text = str(candidate).strip()
    if not candidate_text:
        return None

    if candidate_text in PROFILE_KEY_ALIASES:
        return PROFILE_KEY_ALIASES[candidate_text]

    for profile_key, definition in PROFILE_DEFINITIONS.items():
        aliases = {profile_key, definition["label"], definition["sheet"], *definition.get("aliases", ())}
        if candidate_text in aliases:
            return profile_key

    return candidate_text


def _build_field_section(metadata: Mapping[str, Any], fields: list[tuple[str, str, tuple[str, ...]]]) -> dict[str, Any]:
    section: dict[str, Any] = {}
    for field_key, _field_label, aliases in fields:
        value = _lookup_value(metadata, field_key, *aliases)
        if _is_present(value):
            section[field_key] = _normalize_scalar(value)
    return section


def _merge_sections(base: dict[str, Any], overlay: Mapping[str, Any] | None) -> dict[str, Any]:
    merged = dict(base)
    if not overlay:
        return merged
    for key, value in overlay.items():
        if _is_present(value):
            merged[key] = _normalize_scalar(value)
    return merged


def _resolve_profile_key(
    metadata: Mapping[str, Any],
    *,
    profile_hint: str | None = None,
    asset_resource_type: str | None = None,
) -> str:
    candidates = [
        profile_hint,
        _lookup_value(metadata, "metadata_profile", "profile", "image_category", "image_category_label"),
        _lookup_value(metadata, "object_profile"),
    ]

    for candidate in candidates:
        normalized_candidate = _canonicalize_profile_key(candidate)
        if normalized_candidate in PROFILE_DEFINITIONS:
            return normalized_candidate

    for profile_key, definition in PROFILE_DEFINITIONS.items():
        if profile_key == "other":
            continue
        for field_key, field_label, aliases in definition["fields"]:
            if _lookup_value(metadata, field_key, field_label, *aliases) is not None:
                return profile_key

    return "other"


def _build_core_section(
    *,
    asset_id: int | None,
    asset_filename: str | None,
    asset_status: str | None,
    asset_resource_type: str | None,
    asset_visibility_scope: str | None,
    asset_collection_object_id: int | None,
    asset_created_at: datetime | None,
    metadata: Mapping[str, Any],
    profile_key: str,
) -> dict[str, Any]:
    resource_type = asset_resource_type or str(_lookup_value(metadata, "resource_type") or "image_2d_cultural_object")
    title = _lookup_value(metadata, "title", "image_name", "object_name", "resource_title") or asset_filename or "Untitled Asset"

    core = {
        "resource_id": f"asset-{asset_id}" if asset_id is not None else _lookup_value(metadata, "resource_id") or _lookup_value(metadata, "id"),
        "source_system": _lookup_value(metadata, "source_system") or SOURCE_SYSTEM,
        "source_label": _lookup_value(metadata, "source_label") or SOURCE_LABEL,
        "resource_type": resource_type,
        "resource_type_label": RESOURCE_TYPE_LABELS.get(resource_type, resource_type),
        "title": title,
        "status": asset_status or _lookup_value(metadata, "status") or "processing",
        "preview_enabled": bool(asset_status == "ready" if asset_status is not None else _lookup_value(metadata, "preview_enabled")),
        "visibility_scope": asset_visibility_scope or _lookup_value(metadata, "visibility_scope") or "open",
        "collection_object_id": asset_collection_object_id if asset_collection_object_id is not None else _lookup_value(metadata, "collection_object_id"),
        "profile_key": profile_key,
        "profile_label": PROFILE_DEFINITIONS[profile_key]["label"],
        "profile_sheet": PROFILE_DEFINITIONS[profile_key]["sheet"],
    }
    if asset_created_at is not None:
        core["created_at"] = asset_created_at.isoformat()
    else:
        created_at = _lookup_value(metadata, "created_at")
        if created_at is not None:
            core["created_at"] = _normalize_scalar(created_at)
    return core


def _build_technical_section(
    *,
    metadata: Mapping[str, Any],
    asset_filename: str | None,
    asset_file_path: str | None,
    asset_file_size: int | None,
    asset_mime_type: str | None,
) -> dict[str, Any]:
    technical = _build_field_section(metadata, TECHNICAL_FIELDS)

    if asset_filename and not technical.get("original_file_name"):
        technical["original_file_name"] = asset_filename

    if asset_file_path and not technical.get("image_file_name"):
        technical["image_file_name"] = asset_file_path.rsplit("\\", 1)[-1].rsplit("/", 1)[-1]

    if asset_file_size is not None and not technical.get("file_size"):
        technical["file_size"] = asset_file_size

    if asset_mime_type and not technical.get("format_name"):
        technical["format_name"] = asset_mime_type
        technical.setdefault("original_mime_type", asset_mime_type)

    derivative_policy = infer_derivative_policy_from_metadata(
        {
            **dict(metadata),
            "technical": technical,
        }
    )
    for key, value in derivative_policy.items():
        if value not in (None, "") and not technical.get(key):
            technical[key] = value

    if technical.get("fixity_sha256") and not technical.get("checksum"):
        technical["checksum"] = technical["fixity_sha256"]
        technical.setdefault("checksum_algorithm", "SHA256")

    return technical


def _build_management_section(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return _build_field_section(metadata, MANAGEMENT_FIELDS)


def _build_profile_section(metadata: Mapping[str, Any], profile_key: str) -> dict[str, Any]:
    profile_definition = PROFILE_DEFINITIONS[profile_key]
    return _build_field_section(metadata, profile_definition["fields"])


def build_metadata_layers(
    *,
    asset_id: int | None = None,
    asset_filename: str | None = None,
    asset_file_path: str | None = None,
    asset_file_size: int | None = None,
    asset_mime_type: str | None = None,
    asset_status: str | None = None,
    asset_resource_type: str | None = None,
    asset_visibility_scope: str | None = None,
    asset_collection_object_id: int | None = None,
    asset_created_at: datetime | None = None,
    metadata: Mapping[str, Any] | None = None,
    source_metadata: Mapping[str, Any] | None = None,
    profile_hint: str | None = None,
) -> dict[str, Any]:
    source = _as_dict(metadata)
    layered = _is_layered_metadata(source)

    if layered:
        core_base = _as_dict(source.get("core"))
        management_base = _as_dict(source.get("management"))
        technical_base = _as_dict(source.get("technical"))
        profile_base = _as_dict(source.get("profile"))
        raw_base = _as_dict(source.get("raw_metadata"))
        fallback = {key: value for key, value in source.items() if key not in SECTION_KEYS}
    else:
        core_base = {}
        management_base = {}
        technical_base = {}
        profile_base = {}
        raw_base = {}
        fallback = source

    profile_key = _resolve_profile_key(
        source,
        profile_hint=profile_hint,
        asset_resource_type=asset_resource_type or str(_lookup_value(source, "resource_type") or ""),
    )

    if profile_base.get("key"):
        normalized_profile_key = _canonicalize_profile_key(profile_base["key"])
        if normalized_profile_key:
            profile_key = normalized_profile_key

    profile_key = profile_key if profile_key in PROFILE_DEFINITIONS else "other"
    profile_definition = PROFILE_DEFINITIONS[profile_key]

    core = _merge_sections(
        _build_core_section(
            asset_id=asset_id,
            asset_filename=asset_filename,
            asset_status=asset_status,
            asset_resource_type=asset_resource_type,
            asset_visibility_scope=asset_visibility_scope,
            asset_collection_object_id=asset_collection_object_id,
            asset_created_at=asset_created_at,
            metadata=source,
            profile_key=profile_key,
        ),
        core_base,
    )

    management = _merge_sections(_build_management_section(source), management_base)
    technical = _merge_sections(
        _build_technical_section(
            metadata=source,
            asset_filename=asset_filename,
            asset_file_path=asset_file_path,
            asset_file_size=asset_file_size,
            asset_mime_type=asset_mime_type,
        ),
        technical_base,
    )

    profile_fields = _merge_sections(
        _build_profile_section(source, profile_key),
        profile_base.get("fields") if isinstance(profile_base.get("fields"), Mapping) else None,
    )
    profile = {
        "key": profile_key,
        "label": profile_base.get("label") or profile_definition["label"],
        "sheet": profile_base.get("sheet") or profile_definition["sheet"],
        "fields": profile_fields,
    }

    raw_metadata = deepcopy(source_metadata if source_metadata is not None else raw_base or fallback)

    return {
        "schema_version": METADATA_SCHEMA_VERSION,
        "core": core,
        "management": management,
        "technical": technical,
        "profile": profile,
        "raw_metadata": raw_metadata,
    }


def get_metadata_layers(
    *,
    asset_id: int | None = None,
    asset_filename: str | None = None,
    asset_file_path: str | None = None,
    asset_file_size: int | None = None,
    asset_mime_type: str | None = None,
    asset_status: str | None = None,
    asset_resource_type: str | None = None,
    asset_visibility_scope: str | None = None,
    asset_collection_object_id: int | None = None,
    asset_created_at: datetime | None = None,
    metadata: Mapping[str, Any] | None = None,
    source_metadata: Mapping[str, Any] | None = None,
    profile_hint: str | None = None,
) -> dict[str, Any]:
    return build_metadata_layers(
        asset_id=asset_id,
        asset_filename=asset_filename,
        asset_file_path=asset_file_path,
        asset_file_size=asset_file_size,
        asset_mime_type=asset_mime_type,
        asset_status=asset_status,
        asset_resource_type=asset_resource_type,
        asset_visibility_scope=asset_visibility_scope,
        asset_collection_object_id=asset_collection_object_id,
        asset_created_at=asset_created_at,
        metadata=metadata,
        source_metadata=source_metadata,
        profile_hint=profile_hint,
    )


def get_technical_metadata(layers_or_metadata: Mapping[str, Any] | None) -> dict[str, Any]:
    if not layers_or_metadata:
        return {}
    return build_metadata_layers(metadata=layers_or_metadata)["technical"]


def get_original_file_path(layers_or_metadata: Mapping[str, Any] | None) -> str | None:
    technical = get_technical_metadata(layers_or_metadata)
    value = technical.get("original_file_path")
    return str(value) if value not in (None, "") else None


def get_iiif_access_file_path(layers_or_metadata: Mapping[str, Any] | None) -> str | None:
    technical = get_technical_metadata(layers_or_metadata)
    for key in ("iiif_access_file_path", "preview_file_path"):
        value = technical.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def get_fixity_sha256(layers_or_metadata: Mapping[str, Any] | None) -> str | None:
    technical = get_technical_metadata(layers_or_metadata)
    for key in ("fixity_sha256", "checksum"):
        value = technical.get(key)
        if value not in (None, ""):
            return str(value)
    return None


def get_dimensions(layers_or_metadata: Mapping[str, Any] | None) -> tuple[int, int]:
    technical = get_technical_metadata(layers_or_metadata)

    def _coerce_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    return _coerce_int(technical.get("width")), _coerce_int(technical.get("height"))


def build_iiif_metadata_entries(layers_or_metadata: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not layers_or_metadata:
        return []

    layers = layers_or_metadata if _is_layered_metadata(layers_or_metadata) else build_metadata_layers(metadata=layers_or_metadata)

    def _render_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, (list, tuple, set)):
            return ", ".join(_render_value(item) for item in value if item not in (None, ""))
        if isinstance(value, Mapping):
            return str(dict(value))
        return str(value)

    entries: list[dict[str, Any]] = []
    section_labels = {
        "core": "Platform Core",
        "management": "Shared Management Metadata",
        "technical": "Technical Image Metadata",
    }

    for section_key in ("core", "management", "technical"):
        section = _as_dict(layers.get(section_key))
        for key, value in section.items():
            rendered = _render_value(value)
            if not rendered:
                continue
            entries.append(
                {
                    "label": {"en": [f"{section_labels[section_key]} / {CORE_FIELD_LABELS.get(key, FIELD_LABELS.get(key, key))}"]},
                    "value": {"en": [rendered]},
                }
            )

    profile = _as_dict(layers.get("profile"))
    profile_fields = _as_dict(profile.get("fields"))
    profile_label = profile.get("label") or "Profile"
    for key, value in profile_fields.items():
        rendered = _render_value(value)
        if not rendered:
            continue
        entries.append(
            {
                "label": {"en": [f"{profile_label} / {FIELD_LABELS.get(key, key)}"]},
                "value": {"en": [rendered]},
            }
        )

    return entries
