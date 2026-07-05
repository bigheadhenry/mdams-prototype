/**
 * 元数字段中英文标签映射表
 * 供 AssetDetail、UnifiedResourceDetail 等详情组件共享使用。
 */
export const metadataLabelMap: Record<string, string> = {
  // Core
  source_system: '来源系统',
  source_id: '来源资源 ID',
  source_label: '来源名称',
  resource_type: '资源类型',
  resource_type_label: '资源类型名称',
  visibility_scope: '可见范围',
  collection_object_id: '馆藏对象 ID',
  title: '标题',
  status: '状态',
  preview_enabled: '是否可预览',
  profile_key: '元数据模板键',
  profile_label: '元数据模板',
  profile_sheet: '元数据模板表',
  created_at: '创建时间',

  // Management
  project_type: '项目类型',
  project_name: '项目名称',
  photographer: '摄影师',
  photographer_org: '摄影师单位',
  copyright_owner: '版权所属',
  capture_time: '拍摄时间',
  image_category: '影像类型',
  image_name: '影像名称',
  capture_content: '拍摄内容',
  representative_image: '代表影像',
  remark: '备注',
  tags: '标签',
  record_account: '录入账号',
  record_time: '录入时间',
  image_record_time: '影像录入时间',

  // Technical
  original_file_name: '原始文件名',
  image_file_name: '影像文件名',
  identifier_type: '对象标识符类型',
  identifier_value: '对象标识符值',
  file_size: '文件大小',
  format_name: '格式名称',
  format_version: '格式版本',
  registry_name: '标准来源',
  registry_item: '标准条目',
  byte_order: '字节序',
  checksum_algorithm: '校验算法',
  checksum: '校验值',
  checksum_generator: '校验生成器',
  width: '宽度',
  height: '高度',
  color_space: '色彩空间',
  ingest_method: '入库方式',
  fixity_sha256: 'SHA256',
  conversion_method: '转换方式',
  original_file_path: '原始文件路径',
  original_file_size: '原始文件大小',
  original_mime_type: '原始 MIME 类型',
  error_message: '错误信息',

  // Profile — movable_artifact
  object_number: '文物号',
  object_name: '文物名称',
  object_level: '文物级别',
  object_category: '文物类别',
  object_subcategory: '文物细类',
  management_group: '管理科组',
  photographer_phone: '提照人员电话',
  visible_to_custodians_only: '仅藏品管理者可见',

  // Profile — immovable_artifact
  region_level_1: '一级区域',
  region_level_2: '二级区域',
  building_name: '文物建筑名称',
  orientation: '方位',
  part_level_1: '部位一',
  part_level_2: '部位二',
  part_level_3: '部位三',
  building_component: '建筑构件',

  // Profile — art_photography
  art_photography_type: '艺术摄影类型',
  collection_type: '藏品类型',
  palace_area: '所在宫区',
  season: '季节',
  plant: '植物',
  animal: '动物',
  solar_term: '节气',
  other: '其他',
  theme: '主题',
  cultural_topic: '文化专题',
  exhibition_topic: '展览专题',

  // Profile — business_activity
  main_location: '主要地点',
  main_person: '主要人物',

  // Profile — panorama
  panorama_type: '全景类型',
  location: '位置',

  // Profile — ancient_tree
  archive_number: '档案编号',
  plant_type: '植物类型',
  plant_name: '植物名称',
  region: '所在区域',
  specific_location: '具体位置',
  grade: '等级',

  // Profile — archaeology
  archaeology_image_category: '考古影像分类',

  // Rights
  copyright_status: '版权状态',
  license: '许可协议',
  license_url: '许可协议链接',
  allowed_usage: '允许用途',
  rights_holder: '权利持有人',
  permission_notes: '权限说明',
  usage_restrictions: '使用限制',
  allow_derivatives: '允许衍生',
};

/**
 * 获取字段的中文标签。未匹配到时返回原始 key。
 */
export const getFieldLabel = (key: string): string =>
  metadataLabelMap[key] || key;
