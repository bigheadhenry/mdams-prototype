from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping, Sequence

from .three_d_storage import normalize_three_d_role, summarize_three_d_files, three_d_role_label


METADATA_SCHEMA_VERSION = '1.1'
SOURCE_SYSTEM = 'three_d'
SOURCE_LABEL = '三维数据子系统'

RESOURCE_TYPE_LABELS = {
    'three_d_model': '三维模型',
    'three_d_point_cloud': '点云',
    'three_d_oblique_photo': '倾斜摄影图像',
    'three_d_package': '三维资源包',
    'other': '其他',
}

RESOURCE_TYPE_BY_PROFILE = {
    'model': 'three_d_model',
    'point_cloud': 'three_d_point_cloud',
    'oblique_photo': 'three_d_oblique_photo',
    'package': 'three_d_package',
    'other': 'other',
}

PROFILE_DEFINITIONS: dict[str, dict[str, Any]] = {
    'model': {
        'label': '三维模型',
        'sheet': '三维模型',
        'aliases': ('model', 'glb', 'gltf', 'obj', 'fbx', 'stl', 'usdz'),
        'fields': [
            ('title', '名称', ('name', 'model_name')),
            ('format_name', '格式名称', ('format_name',)),
            ('vertex_count', '顶点数', ('vertex_count',)),
            ('face_count', '面数', ('face_count',)),
            ('material_count', '材质数', ('material_count',)),
            ('texture_count', '贴图数', ('texture_count',)),
            ('lod_count', 'LOD 层级', ('lod_count',)),
        ],
    },
    'point_cloud': {
        'label': '点云',
        'sheet': '点云',
        'aliases': ('point_cloud', 'ply', 'las', 'laz', 'xyz', 'pts'),
        'fields': [
            ('title', '名称', ('name', 'scan_name')),
            ('format_name', '格式名称', ('format_name',)),
            ('point_count', '点数', ('point_count',)),
            ('coordinate_system', '坐标系', ('coordinate_system',)),
            ('unit', '单位', ('unit',)),
        ],
    },
    'oblique_photo': {
        'label': '倾斜摄影图像',
        'sheet': '倾斜摄影图像',
        'aliases': ('oblique_photo', 'oblique', 'scene', 'photo', 'image'),
        'fields': [
            ('title', '名称', ('name', 'scene_name')),
            ('project_name', '项目名称', ('project_name',)),
            ('creator', '创建者', ('creator',)),
            ('capture_time', '采集时间', ('capture_time',)),
        ],
    },
    'package': {
        'label': '三维资源包',
        'sheet': '三维资源包',
        'aliases': ('package', 'bundle', 'zip'),
        'fields': [
            ('title', '名称', ('name', 'package_name')),
            ('project_name', '项目名称', ('project_name',)),
            ('creator', '创建者', ('creator',)),
            ('file_count', '文件数', ('file_count',)),
            ('role_summary', '文件构成', ('role_summary',)),
        ],
    },
    'other': {
        'label': '其他',
        'sheet': '其他',
        'aliases': ('other',),
        'fields': [],
    },
}

PROFILE_KEY_BY_RESOURCE_TYPE = {value: key for key, value in RESOURCE_TYPE_BY_PROFILE.items()}

COLLECTION_FIELDS: list[tuple[str, str, tuple[str, ...]]] = [
    ('collection_object_id', '藏品对象ID', ('collection_object_id',)),
    ('object_number', '藏品号', ('object_number', 'collection_number')),
    ('object_name', '藏品名称', ('object_name', 'collection_name')),
    ('object_type', '藏品类型', ('object_type', 'collection_type')),
    ('collection_unit', '收藏单位', ('collection_unit',)),
    ('summary', '对象摘要', ('object_summary', 'summary')),
    ('keywords', '关键词', ('object_keywords', 'keywords')),
]

PRESERVATION_FIELDS: list[tuple[str, str, tuple[str, ...]]] = [
    ('storage_tier', '存储层级', ('storage_tier',)),
    ('preservation_status', '保存状态', ('preservation_status',)),
    ('preservation_note', '保存说明', ('preservation_note',)),
]


def _as_dict(value: Mapping[str, Any] | None) -> dict[str, Any]:
    if not value:
        return {}
    return dict(value)


def _normalize_scalar(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _is_present(value: Any) -> bool:
    return value not in (None, '')


def _lookup_value(metadata: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in metadata and _is_present(metadata[key]):
            return metadata[key]

    core = metadata.get('core')
    if isinstance(core, Mapping):
        for key in keys:
            if key in core and _is_present(core[key]):
                return core[key]

    raw = metadata.get('raw_metadata')
    if isinstance(raw, Mapping):
        for key in keys:
            if key in raw and _is_present(raw[key]):
                return raw[key]

    profile = metadata.get('profile')
    if isinstance(profile, Mapping):
        fields = profile.get('fields')
        if isinstance(fields, Mapping):
            for key in keys:
                if key in fields and _is_present(fields[key]):
                    return fields[key]

    collection = metadata.get('collection')
    if isinstance(collection, Mapping):
        for key in keys:
            if key in collection and _is_present(collection[key]):
                return collection[key]

    preservation = metadata.get('preservation')
    if isinstance(preservation, Mapping):
        for key in keys:
            if key in preservation and _is_present(preservation[key]):
                return preservation[key]

    return None


def _build_field_section(metadata: Mapping[str, Any], fields: list[tuple[str, str, tuple[str, ...]]]) -> dict[str, Any]:
    section: dict[str, Any] = {}
    for field_key, _field_label, aliases in fields:
        value = _lookup_value(metadata, field_key, *aliases)
        if _is_present(value):
            section[field_key] = _normalize_scalar(value)
    return section


def _resolve_profile_key(
    metadata: Mapping[str, Any],
    *,
    profile_hint: str | None = None,
    asset_filename: str | None = None,
    file_records: Sequence[Mapping[str, Any]] | None = None,
) -> str:
    if file_records:
        roles = {normalize_three_d_role(str(record.get('role'))) for record in file_records if record.get('role')}
        roles.discard('other')
        if len(roles) > 1:
            return 'package'
        if len(roles) == 1:
            return roles.pop()

    candidates = [profile_hint, _lookup_value(metadata, 'three_d_profile', 'profile', 'resource_profile', '三维类型')]
    for candidate in candidates:
        if not candidate:
            continue
        candidate_text = str(candidate).strip().lower()
        if not candidate_text:
            continue
        for profile_key, definition in PROFILE_DEFINITIONS.items():
            aliases = {profile_key, definition['label'].lower(), definition['sheet'].lower(), *{str(alias).lower() for alias in definition.get('aliases', ())}}
            if candidate_text in aliases:
                return profile_key

    filename = (asset_filename or _lookup_value(metadata, 'file_name', 'filename', 'original_file_name') or '').lower()
    extension = filename.rsplit('.', 1)[-1] if '.' in filename else ''
    for profile_key, definition in PROFILE_DEFINITIONS.items():
        if profile_key == 'other':
            continue
        if extension and extension in definition.get('aliases', ()):  # type: ignore[arg-type]
            return profile_key

    for profile_key, definition in PROFILE_DEFINITIONS.items():
        if profile_key == 'other':
            continue
        for field_key, field_label, aliases in definition['fields']:
            if _lookup_value(metadata, field_key, field_label, *aliases) is not None:
                return profile_key

    return 'other'


def _infer_resource_type(profile_key: str, file_records: Sequence[Mapping[str, Any]] | None = None) -> str:
    if file_records:
        roles = {normalize_three_d_role(str(record.get('role'))) for record in file_records if record.get('role')}
        roles.discard('other')
        if len(roles) > 1:
            return 'three_d_package'
        if len(roles) == 1:
            return RESOURCE_TYPE_BY_PROFILE.get(next(iter(roles)), 'other')
    return RESOURCE_TYPE_BY_PROFILE.get(profile_key, 'other')


def build_three_d_metadata_layers(
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
    file_records: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    source = _as_dict(metadata)
    raw_base = _as_dict(source.get('raw_metadata')) if 'raw_metadata' in source else {}

    profile_key = _resolve_profile_key(source, profile_hint=profile_hint, asset_filename=asset_filename, file_records=file_records)
    profile_definition = PROFILE_DEFINITIONS[profile_key]
    resource_type = asset_resource_type or str(_lookup_value(source, 'resource_type') or _infer_resource_type(profile_key, file_records=file_records))
    title = _lookup_value(source, 'title', 'name', 'model_name', 'scene_name', 'package_name') or asset_filename or '未命名三维资源'

    saved_files = [dict(record) for record in file_records or []]
    file_groups, role_summary = summarize_three_d_files(saved_files)
    primary_file = next((record for record in saved_files if record.get('is_primary')), None)
    if primary_file is None and saved_files:
        primary_file = saved_files[0]

    core = {
        'source_id': str(asset_id) if asset_id is not None else _lookup_value(source, 'source_id') or _lookup_value(source, 'id'),
        'source_system': SOURCE_SYSTEM,
        'source_label': SOURCE_LABEL,
        'resource_type': resource_type,
        'resource_type_label': RESOURCE_TYPE_LABELS.get(resource_type, resource_type),
        'title': title,
        'status': asset_status or _lookup_value(source, 'status') or 'processing',
        'preview_enabled': False,
        'profile_key': profile_key,
        'profile_label': profile_definition['label'],
        'profile_sheet': profile_definition['sheet'],
        'collection_object_id': _lookup_value(source, 'collection_object_id'),
        'resource_group': _lookup_value(source, 'resource_group', 'group_key', 'series_key'),
        'version_label': _lookup_value(source, 'version_label') or 'original',
        'version_order': _lookup_value(source, 'version_order') or 0,
        'is_current': bool(_lookup_value(source, 'is_current')) if _lookup_value(source, 'is_current') is not None else True,
        'is_web_preview': bool(_lookup_value(source, 'is_web_preview')) if _lookup_value(source, 'is_web_preview') is not None else False,
        'web_preview_status': _lookup_value(source, 'web_preview_status') or 'disabled',
        'web_preview_reason': _lookup_value(source, 'web_preview_reason'),
    }
    if asset_created_at is not None:
        core['created_at'] = asset_created_at.isoformat()

    management = _build_field_section(
        source,
        [
            ('project_name', '项目名称', ('project_name',)),
            ('creator', '创建者', ('creator',)),
            ('creator_org', '创建者单位', ('creator_org',)),
            ('capture_time', '采集时间', ('capture_time',)),
            ('remark', '备注', ('remark',)),
            ('tags', '标签', ('tags',)),
        ],
    )

    collection = _build_field_section(source, COLLECTION_FIELDS)
    preservation = _build_field_section(source, PRESERVATION_FIELDS)

    technical = _build_field_section(
        source,
        [
            ('original_file_name', '原始文件名', ('file_name', 'filename')),
            ('file_size', '文件大小', ('file_size',)),
            ('format_name', '格式名称', ('format_name',)),
            ('format_version', '格式版本', ('format_version',)),
            ('extension', '扩展名', ('extension',)),
            ('vertex_count', '顶点数', ('vertex_count',)),
            ('face_count', '面数', ('face_count',)),
            ('material_count', '材质数', ('material_count',)),
            ('texture_count', '贴图数', ('texture_count',)),
            ('point_count', '点数', ('point_count',)),
            ('lod_count', 'LOD 层级', ('lod_count',)),
            ('coordinate_system', '坐标系', ('coordinate_system',)),
            ('unit', '单位', ('unit',)),
            ('scale', '比例', ('scale',)),
            ('bounding_box', '包围盒', ('bounding_box',)),
            ('checksum_algorithm', '校验算法', ('checksum_algorithm',)),
            ('checksum', '校验值', ('checksum', 'sha256')),
            ('ingest_method', '入库方式', ('ingest_method',)),
        ],
    )

    if asset_filename and not technical.get('original_file_name'):
        technical['original_file_name'] = asset_filename
    if asset_file_path and not technical.get('file_path'):
        technical['file_path'] = asset_file_path
    if asset_file_size is not None and not technical.get('file_size'):
        technical['file_size'] = asset_file_size
    if asset_mime_type and not technical.get('format_name'):
        technical['format_name'] = asset_mime_type

    if saved_files:
        technical['files'] = saved_files
        technical['file_count'] = len(saved_files)
        technical['file_groups'] = file_groups
        technical['primary_file'] = primary_file
        technical['primary_file_role'] = primary_file.get('role') if primary_file else None
        technical['role_summary'] = role_summary

    profile = {
        'key': profile_key,
        'label': profile_definition['label'],
        'sheet': profile_definition['sheet'],
        'fields': _build_field_section(source, profile_definition['fields']),
    }

    if profile_key == 'package':
        profile['fields']['file_count'] = len(saved_files)
        profile['fields']['role_summary'] = role_summary

    raw_metadata = deepcopy(source_metadata if source_metadata is not None else raw_base or source)

    return {
        'schema_version': METADATA_SCHEMA_VERSION,
        'core': core,
        'management': management,
        'collection': collection,
        'technical': technical,
        'profile': profile,
        'preservation': preservation,
        'raw_metadata': raw_metadata,
    }
