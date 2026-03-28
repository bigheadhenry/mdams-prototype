from __future__ import annotations

from ..schemas import (
    ThreeDMetadataDictionaryResponse,
    ThreeDMetadataDictionarySection,
    ThreeDMetadataFieldDefinition,
)


THREE_D_METADATA_DICTIONARY = ThreeDMetadataDictionaryResponse(
    schema_version='1.0',
    sections=[
        ThreeDMetadataDictionarySection(
            key='core',
            label='核心元数据',
            fields=[
                ThreeDMetadataFieldDefinition(key='title', label='三维对象名称', required=True, layer='core', description='三维资源对象的显示名称'),
                ThreeDMetadataFieldDefinition(key='resource_group', label='资源组', required=True, layer='core', description='同一数字对象的版本集合标识'),
                ThreeDMetadataFieldDefinition(key='version_label', label='版本号', required=True, layer='core', description='original / v1 / v2 等版本标签'),
                ThreeDMetadataFieldDefinition(key='version_order', label='版本顺序', required=True, layer='core', description='版本排序整数'),
                ThreeDMetadataFieldDefinition(key='is_web_preview', label='允许 Web 展示', required=True, layer='core', description='是否允许作为 Web 展示版本'),
                ThreeDMetadataFieldDefinition(key='web_preview_status', label='Web 展示状态', required=True, layer='core', description='ready / pending / disabled'),
            ],
        ),
        ThreeDMetadataDictionarySection(
            key='collection',
            label='藏品关联元数据',
            fields=[
                ThreeDMetadataFieldDefinition(key='object_number', label='藏品号', required=False, layer='collection', description='与博物馆藏品库关联的编号'),
                ThreeDMetadataFieldDefinition(key='object_name', label='藏品名称', required=False, layer='collection', description='与博物馆藏品库关联的名称'),
                ThreeDMetadataFieldDefinition(key='object_type', label='藏品类型', required=False, layer='collection', description='可移动文物、不可移动文物等'),
                ThreeDMetadataFieldDefinition(key='collection_unit', label='收藏单位', required=False, layer='collection', description='藏品所属单位或部门'),
            ],
        ),
        ThreeDMetadataDictionarySection(
            key='technical',
            label='技术元数据',
            fields=[
                ThreeDMetadataFieldDefinition(key='format_name', label='格式名称', required=False, layer='technical'),
                ThreeDMetadataFieldDefinition(key='vertex_count', label='顶点数', required=False, layer='technical'),
                ThreeDMetadataFieldDefinition(key='face_count', label='面数', required=False, layer='technical'),
                ThreeDMetadataFieldDefinition(key='point_count', label='点数', required=False, layer='technical'),
                ThreeDMetadataFieldDefinition(key='coordinate_system', label='坐标系', required=False, layer='technical'),
                ThreeDMetadataFieldDefinition(key='unit', label='单位', required=False, layer='technical'),
            ],
        ),
        ThreeDMetadataDictionarySection(
            key='management',
            label='管理元数据',
            fields=[
                ThreeDMetadataFieldDefinition(key='project_name', label='项目名称', required=False, layer='management'),
                ThreeDMetadataFieldDefinition(key='creator', label='创建者', required=False, layer='management'),
                ThreeDMetadataFieldDefinition(key='creator_org', label='创建者单位', required=False, layer='management'),
                ThreeDMetadataFieldDefinition(key='capture_time', label='采集时间', required=False, layer='management'),
                ThreeDMetadataFieldDefinition(key='tags', label='标签', required=False, layer='management'),
            ],
        ),
        ThreeDMetadataDictionarySection(
            key='preservation',
            label='保存元数据',
            fields=[
                ThreeDMetadataFieldDefinition(key='storage_tier', label='存储层级', required=True, layer='preservation', description='working / delivery / archive'),
                ThreeDMetadataFieldDefinition(key='preservation_status', label='保存状态', required=True, layer='preservation', description='pending / preserved / archived'),
                ThreeDMetadataFieldDefinition(key='preservation_note', label='保存说明', required=False, layer='preservation'),
            ],
        ),
        ThreeDMetadataDictionarySection(
            key='production',
            label='生产链路元数据',
            fields=[
                ThreeDMetadataFieldDefinition(key='stage', label='阶段', required=True, layer='production', description='采集 / 处理 / 发布 / 质检 / 保存'),
                ThreeDMetadataFieldDefinition(key='event_type', label='事件类型', required=True, layer='production'),
                ThreeDMetadataFieldDefinition(key='status', label='事件状态', required=True, layer='production'),
                ThreeDMetadataFieldDefinition(key='actor', label='执行人', required=False, layer='production'),
                ThreeDMetadataFieldDefinition(key='evidence', label='证据', required=False, layer='production'),
            ],
        ),
    ],
)


def build_three_d_metadata_dictionary() -> ThreeDMetadataDictionaryResponse:
    return THREE_D_METADATA_DICTIONARY
