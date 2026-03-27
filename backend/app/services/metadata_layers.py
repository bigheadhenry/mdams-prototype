from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping


METADATA_SCHEMA_VERSION = "2.0"
SOURCE_SYSTEM = "mdams_2d_image_subsystem"
SOURCE_LABEL = "二维影像子系统"

RESOURCE_TYPE_LABELS = {
    "image_2d_cultural_object": "二维图像文物资源",
}

SECTION_KEYS = {"core", "management", "technical", "raw_metadata"}

MANAGEMENT_FIELDS: list[tuple[str, str, tuple[str, ...]]] = [
    ("project_type", "项目类型", ("项目类型",)),
    ("project_name", "项目名称", ("项目名称",)),
    ("photographer", "摄影者/制作者", ("摄影者/制作者",)),
    ("photographer_org", "摄影者/制作者单位", ("摄影者/制作者单位",)),
    ("copyright_owner", "版权所有", ("版权所有",)),
    ("capture_time", "拍摄/制作时间", ("拍摄/制作时间",)),
    ("image_category", "影像类别", ("影像类别",)),
    ("image_name", "影像名称", ("影像名称",)),
    ("capture_content", "拍摄/制作内容", ("拍摄/制作内容",)),
    ("representative_image", "是否为代表影像", ("是否为代表影像",)),
    ("remark", "备注", ("备注",)),
    ("tags", "影像标签", ("影像标签",)),
    ("record_account", "属性录入账号", ("属性录入账号",)),
    ("record_time", "属性录入时间", ("属性录入时间",)),
    ("image_record_time", "影像录入时间", ("影像录入时间",)),
]

TECHNICAL_FIELDS: list[tuple[str, str, tuple[str, ...]]] = [
    ("original_file_name", "原始文件名", ("原始文件名", "original_filename")),
    ("image_file_name", "影像文件名", ("影像文件名",)),
    ("identifier_type", "对象标识符类型", ("对象标识符类型",)),
    ("identifier_value", "对象标识符值", ("对象标识符值",)),
    ("file_size", "文件大小", ("文件大小",)),
    ("format_name", "格式名称", ("格式名称",)),
    ("format_version", "格式版本", ("格式版本",)),
    ("registry_name", "格式注册表名称", ("格式注册表名称",)),
    ("registry_item", "格式注册表项", ("格式注册表项",)),
    ("byte_order", "字节顺序", ("字节顺序",)),
    ("checksum_algorithm", "消息摘要算法", ("消息摘要算法",)),
    ("checksum", "消息摘要", ("消息摘要", "sha256", "SHA256")),
    ("checksum_generator", "消息摘要生成器", ("消息摘要生成器",)),
    ("width", "图像宽度", ("图像宽度",)),
    ("height", "图像高度", ("图像高度",)),
    ("color_space", "色彩空间", ("色彩空间",)),
    ("ingest_method", "入库方式", ("入库方式",)),
    ("fixity_sha256", "SHA256校验值", ("SHA256校验值", "sha256", "SHA256")),
    ("conversion_method", "转换方式", ("转换方式",)),
    ("original_file_path", "原始文件路径", ("原始文件路径",)),
    ("original_file_size", "原始文件大小", ("原始文件大小",)),
    ("original_mime_type", "原始 MIME 类型", ("原始 MIME 类型",)),
    ("error_message", "错误信息", ("错误信息",)),
]

PROFILE_DEFINITIONS: dict[str, dict[str, Any]] = {
    "movable_artifact": {
        "label": "可移动文物",
        "sheet": "可移动文物",
        "aliases": ("可移动文物", "image_2d_cultural_object", "cultural_object", "artifact"),
        "fields": [
            ("object_number", "文物号", ("文物号",)),
            ("object_name", "文物名称", ("文物名称",)),
            ("object_level", "文物级别", ("文物级别",)),
            ("object_category", "文物类别", ("文物类别",)),
            ("object_subcategory", "文物细类", ("文物细类",)),
            ("management_group", "管理科组", ("管理科组",)),
            ("photographer", "提照人员", ("提照人员",)),
            ("photographer_phone", "提照人员电话", ("提照人员电话",)),
            ("visible_to_custodians_only", "影像是否只对藏品管理者可见", ("影像是否只对藏品管理者可见",)),
        ],
    },
    "immovable_artifact": {
        "label": "不可移动文物",
        "sheet": "不可移动文物",
        "aliases": ("不可移动文物",),
        "fields": [
            ("region_level_1", "一级区域", ("一级区域",)),
            ("region_level_2", "二级区域", ("二级区域",)),
            ("building_name", "文物建筑名称", ("文物建筑名称",)),
            ("orientation", "方位", ("方位",)),
            ("part_level_1", "部位一", ("部位一",)),
            ("part_level_2", "部位二", ("部位二",)),
            ("part_level_3", "部位三", ("部位三",)),
            ("building_component", "建筑构件", ("建筑构件",)),
        ],
    },
    "art_photography": {
        "label": "艺术摄影",
        "sheet": "艺术摄影",
        "aliases": ("艺术摄影",),
        "fields": [
            ("art_photography_type", "艺术摄影类型", ("艺术摄影类型",)),
            ("collection_type", "藏品类型", ("藏品类型",)),
            ("palace_area", "所在宫区", ("所在宫区",)),
            ("season", "季节", ("季节",)),
            ("plant", "植物", ("植物",)),
            ("animal", "动物", ("动物",)),
            ("solar_term", "节气", ("节气",)),
            ("other", "其他", ("其他",)),
            ("theme", "主题", ("主题",)),
            ("cultural_topic", "文化专题", ("文化专题",)),
            ("exhibition_topic", "展览专题", ("展览专题",)),
        ],
    },
    "business_activity": {
        "label": "业务活动",
        "sheet": "业务活动",
        "aliases": ("业务活动",),
        "fields": [
            ("main_location", "主要地点", ("主要地点",)),
            ("main_person", "主要人物", ("主要人物",)),
        ],
    },
    "panorama": {
        "label": "全景",
        "sheet": "全景",
        "aliases": ("全景",),
        "fields": [
            ("panorama_type", "全景类型", ("全景类型",)),
            ("location", "位置", ("位置",)),
        ],
    },
    "ancient_tree": {
        "label": "古树",
        "sheet": "古树",
        "aliases": ("古树",),
        "fields": [
            ("archive_number", "档案编号", ("档案编号",)),
            ("plant_type", "植物类型", ("植物类型",)),
            ("plant_name", "植物名称", ("植物名称",)),
            ("region", "所在区域", ("所在区域",)),
            ("specific_location", "具体位置", ("具体位置",)),
            ("grade", "等级", ("等级",)),
        ],
    },
    "archaeology": {
        "label": "考古",
        "sheet": "考古",
        "aliases": ("考古",),
        "fields": [
            ("archaeology_image_category", "考古影像分类", ("考古影像分类",)),
        ],
    },
    "other": {
        "label": "其他",
        "sheet": "其他",
        "aliases": ("其他", "other"),
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
    if not value:
        return {}
    return dict(value)


def _is_layered_metadata(metadata: Mapping[str, Any] | None) -> bool:
    if not metadata:
        return False
    return any(key in metadata for key in SECTION_KEYS)


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


def _build_field_section(
    metadata: Mapping[str, Any],
    fields: list[tuple[str, str, tuple[str, ...]]],
) -> dict[str, Any]:
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
        _lookup_value(metadata, "metadata_profile", "profile", "image_category", "影像类别"),
        _lookup_value(metadata, "object_profile", "对象 profile"),
    ]

    for candidate in candidates:
        if not candidate:
            continue
        candidate_text = str(candidate).strip()
        if not candidate_text:
            continue
        for profile_key, definition in PROFILE_DEFINITIONS.items():
            aliases = {profile_key, definition["label"], definition["sheet"], *definition.get("aliases", ())}
            if candidate_text in aliases:
                return profile_key

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
    asset_created_at: datetime | None,
    metadata: Mapping[str, Any],
    profile_key: str,
) -> dict[str, Any]:
    resource_type = asset_resource_type or str(_lookup_value(metadata, "resource_type") or "image_2d_cultural_object")
    title = _lookup_value(metadata, "title", "image_name", "影像名称", "object_name", "文物名称") or asset_filename or "未命名资源"

    core = {
        "resource_id": f"asset-{asset_id}" if asset_id is not None else _lookup_value(metadata, "resource_id") or _lookup_value(metadata, "id"),
        "source_system": _lookup_value(metadata, "source_system") or SOURCE_SYSTEM,
        "source_label": _lookup_value(metadata, "source_label") or SOURCE_LABEL,
        "resource_type": resource_type,
        "resource_type_label": RESOURCE_TYPE_LABELS.get(resource_type, resource_type),
        "title": title,
        "status": asset_status or _lookup_value(metadata, "status") or "processing",
        "preview_enabled": bool(asset_status == "ready" if asset_status is not None else _lookup_value(metadata, "preview_enabled")),
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
    asset_created_at: datetime | None = None,
    metadata: Mapping[str, Any] | None = None,
    source_metadata: Mapping[str, Any] | None = None,
    profile_hint: str | None = None,
) -> dict[str, Any]:
    """Build a layered metadata payload for the 2D image subsystem."""

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
        profile_key = str(profile_base["key"])

    profile_key = profile_key if profile_key in PROFILE_DEFINITIONS else "other"
    profile_definition = PROFILE_DEFINITIONS[profile_key]

    core = _merge_sections(
        _build_core_section(
            asset_id=asset_id,
            asset_filename=asset_filename,
            asset_status=asset_status,
            asset_resource_type=asset_resource_type,
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

    profile_fields = _merge_sections(_build_profile_section(source, profile_key), profile_base.get("fields") if isinstance(profile_base.get("fields"), Mapping) else None)
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

    width = _coerce_int(technical.get("width"))
    height = _coerce_int(technical.get("height"))
    return width, height


def build_iiif_metadata_entries(layers_or_metadata: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not layers_or_metadata:
        return []

    layers = layers_or_metadata if _is_layered_metadata(layers_or_metadata) else build_metadata_layers(metadata=layers_or_metadata)

    def _render_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, bool):
            return "是" if value else "否"
        if isinstance(value, (list, tuple, set)):
            return "、".join(_render_value(item) for item in value if item not in (None, ""))
        if isinstance(value, Mapping):
            return str(dict(value))
        return str(value)

    entries: list[dict[str, Any]] = []
    section_labels = {
        "core": "平台核心",
        "management": "共用管理元数据",
        "technical": "技术影像元数据",
    }

    for section_key in ("core", "management", "technical"):
        section = _as_dict(layers.get(section_key))
        for key, value in section.items():
            rendered = _render_value(value)
            if not rendered:
                continue
            entries.append(
                {
                    "label": {"en": [f"{section_labels[section_key]} / {FIELD_LABELS.get(key, key)}"]},
                    "value": {"en": [rendered]},
                }
            )

    profile = _as_dict(layers.get("profile"))
    profile_fields = _as_dict(profile.get("fields"))
    profile_label = profile.get("label") or "对象 profile"
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
