import { describe, it, expect } from 'vitest';
import { metadataLabelMap, getFieldLabel } from '../metadataLabels';

describe('getFieldLabel', () => {
  it('returns correct Chinese label for a known key', () => {
    expect(getFieldLabel('source_system')).toBe('来源系统');
    expect(getFieldLabel('title')).toBe('标题');
    expect(getFieldLabel('object_number')).toBe('文物号');
    expect(getFieldLabel('copyright_status')).toBe('版权状态');
    expect(getFieldLabel('file_size')).toBe('文件大小');
  });

  it('returns the original key for an unknown key', () => {
    expect(getFieldLabel('nonexistent_key')).toBe('nonexistent_key');
    expect(getFieldLabel('')).toBe('');
    expect(getFieldLabel('foo_bar_baz')).toBe('foo_bar_baz');
  });
});

describe('metadataLabelMap', () => {
  it('contains all core metadata entries', () => {
    expect(metadataLabelMap.source_system).toBe('来源系统');
    expect(metadataLabelMap.source_id).toBe('来源资源 ID');
    expect(metadataLabelMap.title).toBe('标题');
    expect(metadataLabelMap.status).toBe('状态');
    expect(metadataLabelMap.created_at).toBe('创建时间');
  });

  it('contains all management entries', () => {
    expect(metadataLabelMap.project_type).toBe('项目类型');
    expect(metadataLabelMap.project_name).toBe('项目名称');
    expect(metadataLabelMap.photographer).toBe('摄影师');
    expect(metadataLabelMap.copyright_owner).toBe('版权所属');
    expect(metadataLabelMap.remark).toBe('备注');
    expect(metadataLabelMap.record_time).toBe('录入时间');
  });

  it('contains all technical entries', () => {
    expect(metadataLabelMap.original_file_name).toBe('原始文件名');
    expect(metadataLabelMap.format_name).toBe('格式名称');
    expect(metadataLabelMap.width).toBe('宽度');
    expect(metadataLabelMap.height).toBe('高度');
    expect(metadataLabelMap.checksum).toBe('校验值');
    expect(metadataLabelMap.color_space).toBe('色彩空间');
  });

  it('contains all profile entries', () => {
    // movable_artifact
    expect(metadataLabelMap.object_number).toBe('文物号');
    expect(metadataLabelMap.object_name).toBe('文物名称');
    expect(metadataLabelMap.object_level).toBe('文物级别');
    // immovable_artifact
    expect(metadataLabelMap.region_level_1).toBe('一级区域');
    expect(metadataLabelMap.building_name).toBe('文物建筑名称');
    expect(metadataLabelMap.orientation).toBe('方位');
    // art_photography
    expect(metadataLabelMap.art_photography_type).toBe('艺术摄影类型');
    expect(metadataLabelMap.collection_type).toBe('藏品类型');
    expect(metadataLabelMap.season).toBe('季节');
    expect(metadataLabelMap.theme).toBe('主题');
    // business_activity
    expect(metadataLabelMap.main_location).toBe('主要地点');
    expect(metadataLabelMap.main_person).toBe('主要人物');
    // panorama
    expect(metadataLabelMap.panorama_type).toBe('全景类型');
    expect(metadataLabelMap.location).toBe('位置');
    // ancient_tree
    expect(metadataLabelMap.archive_number).toBe('档案编号');
    expect(metadataLabelMap.plant_type).toBe('植物类型');
    expect(metadataLabelMap.plant_name).toBe('植物名称');
    // archaeology
    expect(metadataLabelMap.archaeology_image_category).toBe('考古影像分类');
  });

  it('contains all rights entries', () => {
    expect(metadataLabelMap.copyright_status).toBe('版权状态');
    expect(metadataLabelMap.license).toBe('许可协议');
    expect(metadataLabelMap.rights_holder).toBe('权利持有人');
    expect(metadataLabelMap.allow_derivatives).toBe('允许衍生');
  });

  it('has expected total number of entries', () => {
    // Total known keys from the source file (exact count)
    const expectedKeys = [
      'source_system', 'source_id', 'source_label', 'resource_type',
      'resource_type_label', 'visibility_scope', 'collection_object_id',
      'title', 'status', 'preview_enabled', 'profile_key', 'profile_label',
      'profile_sheet', 'created_at', 'project_type', 'project_name',
      'photographer', 'photographer_org', 'copyright_owner', 'capture_time',
      'image_category', 'image_name', 'capture_content', 'representative_image',
      'remark', 'tags', 'record_account', 'record_time', 'image_record_time',
      'original_file_name', 'image_file_name', 'identifier_type',
      'identifier_value', 'file_size', 'format_name', 'format_version',
      'registry_name', 'registry_item', 'byte_order', 'checksum_algorithm',
      'checksum', 'checksum_generator', 'width', 'height', 'color_space',
      'ingest_method', 'fixity_sha256', 'conversion_method',
      'original_file_path', 'original_file_size', 'original_mime_type',
      'error_message', 'object_number', 'object_name', 'object_level',
      'object_category', 'object_subcategory', 'management_group',
      'photographer_phone', 'visible_to_custodians_only',
      'region_level_1', 'region_level_2', 'building_name', 'orientation',
      'part_level_1', 'part_level_2', 'part_level_3', 'building_component',
      'art_photography_type', 'collection_type', 'palace_area', 'season',
      'plant', 'animal', 'solar_term', 'other', 'theme', 'cultural_topic',
      'exhibition_topic', 'main_location', 'main_person', 'panorama_type',
      'location', 'archive_number', 'plant_type', 'plant_name', 'region',
      'specific_location', 'grade', 'archaeology_image_category',
      'copyright_status', 'license', 'license_url', 'allowed_usage',
      'rights_holder', 'permission_notes', 'usage_restrictions',
      'allow_derivatives',
    ];
    expect(Object.keys(metadataLabelMap)).toEqual(expectedKeys);
    expect(Object.keys(metadataLabelMap)).toHaveLength(expectedKeys.length);
  });
});
