export interface AssetSummary {
  id: number;
  filename: string;
  file_size: number;
  mime_type: string;
  visibility_scope?: string | null;
  collection_object_id?: number | null;
  status: string;
  created_at: string;
}

export interface ImageRecordAssetBinding {
  asset_id: number;
  filename?: string | null;
  status?: string | null;
  created_at?: string | null;
}

export interface ImageRecordValidationState {
  ready_for_submit: boolean;
  missing_fields: string[];
  missing_labels: string[];
}

export interface ImageRecordDuplicateAssetMatch {
  asset_id: number;
  filename?: string | null;
  image_record_id?: number | null;
  status?: string | null;
}

export interface ImageRecordPendingUpload {
  token: string;
  filename: string;
  file_size: number;
  mime_type?: string | null;
  extension?: string | null;
  width?: number | null;
  height?: number | null;
  format_name?: string | null;
  sha256: string;
  uploaded_at: string;
  filename_matches: string[];
  warnings: string[];
  duplicate_assets: ImageRecordDuplicateAssetMatch[];
  can_confirm_bind: boolean;
  can_confirm_replace: boolean;
}

export interface ImageRecordSummary {
  id: number;
  sheet_id?: number | null;
  line_no?: number | null;
  record_no: string;
  title: string;
  status: string;
  resource_type: string;
  visibility_scope: string;
  collection_object_id?: number | null;
  profile_key: string;
  profile_label?: string | null;
  project_name?: string | null;
  image_category?: string | null;
  object_number?: string | null;
  representative_image?: boolean;
  created_by_user_id?: number | null;
  created_by_display_name?: string | null;
  submitted_by_user_id?: number | null;
  submitted_by_display_name?: string | null;
  assigned_photographer_user_id?: number | null;
  assigned_photographer_display_name?: string | null;
  created_at: string;
  updated_at: string;
  submitted_at?: string | null;
  asset?: ImageRecordAssetBinding | null;
}

export interface ImageRecordDetailResponse extends ImageRecordSummary {
  metadata_info: AssetMetadataLayers;
  validation: ImageRecordValidationState;
  pending_upload?: ImageRecordPendingUpload | null;
}

export interface ImageRecordSavePayload {
  record_no?: string | null;
  title?: string | null;
  resource_type?: string | null;
  visibility_scope?: string | null;
  collection_object_id?: number | null;
  profile_key?: string | null;
  management?: Record<string, unknown>;
  profile_fields?: Record<string, unknown>;
  raw_metadata?: Record<string, unknown>;
  assigned_photographer_user_id?: number | null;
}

export interface CulturalObjectLookupRecord {
  object_number: string;
  object_name?: string | null;
  object_level?: string | null;
  object_category?: string | null;
  object_subcategory?: string | null;
  management_group?: string | null;
  source: string;
  source_label: string;
  is_temporary_number: boolean;
}

export interface CulturalObjectLookupResponse {
  query: string;
  normalized_object_number?: string | null;
  found: boolean;
  lookup_status: string;
  message?: string | null;
  record?: CulturalObjectLookupRecord | null;
}

export interface CulturalObjectSampleListResponse {
  total: number;
  items: CulturalObjectLookupRecord[];
}

export interface ImageIngestSheetSavePayload {
  title?: string | null;
  image_type?: string | null;
  project_type?: string | null;
  project_name?: string | null;
  photographer?: string | null;
  photographer_org?: string | null;
  copyright_owner?: string | null;
  capture_time?: string | null;
  remark?: string | null;
  assigned_photographer_user_id?: number | null;
  metadata_info?: Record<string, unknown>;
}

export interface ImageIngestSheetSummary {
  id: number;
  sheet_no: string;
  title?: string | null;
  status: string;
  image_type: string;
  project_type?: string | null;
  project_name?: string | null;
  photographer?: string | null;
  photographer_org?: string | null;
  capture_time?: string | null;
  assigned_photographer_user_id?: number | null;
  assigned_photographer_display_name?: string | null;
  item_count: number;
  uploaded_item_count: number;
  created_at: string;
  updated_at: string;
}

export interface ImageIngestSheetDetailResponse extends ImageIngestSheetSummary {
  copyright_owner?: string | null;
  remark?: string | null;
  metadata_info?: Record<string, unknown>;
  items: ImageRecordSummary[];
}

export interface ApplicationCartItem {
  cartKey: string;
  assetId?: number | null;
  sourceSystem?: string | null;
  sourceId?: string | null;
  resourceType?: string | null;
  title: string;
  manifestUrl: string;
  objectNumber?: string | null;
  era?: string | null;
  objectLevel?: string | null;
  sourceLabel?: string | null;
  canSubmit?: boolean;
  note?: string;
}

export interface ApplicationSummary {
  id: number;
  application_no: string;
  requester_name: string;
  requester_org?: string | null;
  purpose: string;
  usage_scope?: string | null;
  status: string;
  status_label: string;
  review_note?: string | null;
  item_count: number;
  created_at: string;
  submitted_at?: string | null;
  reviewed_at?: string | null;
}

export interface FileRecord {
  role?: string;
  role_label?: string;
  filename?: string;
  file_path?: string;
  mime_type?: string;
  file_size?: number;
  is_current?: boolean;
  is_original?: boolean;
  same_as_primary?: boolean;
  derivation_method?: string | null;
  sha256?: string | null;
  fixity_status?: string | null;
  last_verified_at?: string | null;
}

export interface TimelineEntry {
  step?: string;
  label?: string;
  status?: string;
  status_label?: string;
  description?: string;
}

export interface LifecycleEntry {
  step: string;
  label: string;
  status: string;
  status_label: string;
  description: string;
  timestamp?: string | null;
  evidence?: string | null;
}

export interface AssetDetailResponse {
  id: number;
  identifier: string;
  title: string;
  resource_type: string;
  resource_type_label: string;
  visibility_scope: string;
  collection_object_id?: number | null;
  status: string;
  process_message?: string | null;
  created_at: string;
  file: {
    filename: string;
    file_path: string;
    actual_filename: string;
    file_size: number;
    mime_type: string;
  };
  status_info: {
    code: string;
    label: string;
    message?: string | null;
    preview_ready: boolean;
    has_error: boolean;
  };
  lifecycle: LifecycleEntry[];
  process_timeline: TimelineEntry[];
  structure: {
    summary: string;
    primary_file: FileRecord;
    original_file: FileRecord;
    derivatives: FileRecord[];
    packaging?: {
      bagit_supported?: boolean;
      bagit_note?: string;
    };
  };
  technical_metadata: AssetTechnicalMetadata;
  metadata_layers?: AssetMetadataLayers;
  rights_display?: RightsDisplay | null;
  access: AssetAccessSummary;
  access_paths: {
    manifest?: {
      label?: string;
      url?: string;
    };
    mirador_preview?: {
      label?: string;
      manifest_url?: string;
      enabled?: boolean;
    };
    preview_enabled?: boolean;
  };
  outputs: {
    download_url: string;
    download_bag_url: string;
  };
  output_actions: {
    download_current_file?: {
      label?: string;
      url?: string;
    };
    download_bag?: {
      label?: string;
      url?: string;
    };
  };
}

export interface AssetTechnicalMetadata {
  width?: number;
  height?: number;
  fixity_sha256?: string;
  fixity_status?: string;
  last_verified_at?: string;
  ingest_method?: string;
  conversion_method?: string;
  original_file_path?: string;
  error_message?: string;
  original_file_size?: number;
  original_mime_type?: string;
  [key: string]: unknown;
}

export interface AssetMetadataLayers {
  schema_version?: string;
  core?: Record<string, unknown>;
  management?: Record<string, unknown>;
  technical?: Record<string, unknown>;
  profile?: {
    key?: string;
    label?: string;
    sheet?: string;
    fields?: Record<string, unknown>;
  };
  rights?: Record<string, unknown>;
  rights_display?: RightsDisplay;
  raw_metadata?: Record<string, unknown>;
}

export interface RightsDisplay {
  statement: string;
  credit_line: string;
  license?: string | null;
  license_url?: string | null;
  copyright_status?: string | null;
  usage_restrictions?: string | null;
  allow_derivatives?: boolean | null;
}

export interface FaceRecognitionFaceResult {
  face_index: number;
  name?: string | null;
  recognized: boolean;
  confidence: number;
  score: number;
  bbox: number[];
  cluster_id?: string | null;
}

export interface FaceRecognitionMetadata {
  status: string;
  provider?: string | null;
  threshold?: number | null;
  asset_id?: number | null;
  last_run_at?: string | null;
  face_count?: number;
  recognized_count?: number;
  recognized_names?: string[];
  image_width?: number | null;
  image_height?: number | null;
  faces?: FaceRecognitionFaceResult[];
  error_message?: string | null;
  raw_response?: Record<string, unknown>;
}

export interface AssetAccessSummary {
  manifest_url: string;
  preview_enabled: boolean;
}

export interface MiradorSearchResult {
  asset_id: number;
  title: string;
  manifest_url: string;
  source_system: string;
  source_id: string;
  object_number?: string | null;
  filename?: string | null;
  score?: number;
  reasons?: string[];
}

export interface MiradorToolCall {
  name: string;
  arguments?: Record<string, unknown>;
  version?: string;
}

export interface MiradorAIPlan {
  action:
    | 'zoom_in'
    | 'zoom_out'
    | 'pan_left'
    | 'pan_right'
    | 'pan_up'
    | 'pan_down'
    | 'reset_view'
    | 'fit_to_window'
    | 'search_assets'
    | 'open_compare'
    | 'switch_compare_mode'
    | 'close_compare'
    | 'noop';
  assistant_message: string;
  requires_confirmation?: boolean;
  search_query?: string | null;
  search_results?: MiradorSearchResult[];
  target_asset?: MiradorSearchResult | null;
  compare_mode?: 'single' | 'side_by_side' | null;
  pan_pixels?: number | null;
  zoom_factor?: number | null;
  tool_call?: MiradorToolCall | null;
}

export interface MiradorAIRequest {
  prompt: string;
  current_asset_id?: number | null;
  current_manifest_url?: string | null;
  current_title?: string | null;
  current_object_number?: string | null;
  current_source_system?: string | null;
  current_source_id?: string | null;
  max_candidates?: number;
}

export interface UnifiedResourceSourceSummary {
  source_system: string;
  source_label: string;
  resource_type: string;
  resource_count: number;
  status: string;
  healthy: boolean;
  last_synced_at?: string | null;
  entrypoint: string;
}

export interface UnifiedResourceAction {
  key: string;
  label: string;
  kind: string;
  target: string;
  url?: string | null;
  method?: string;
  enabled: boolean;
  reason?: string | null;
}

export interface UnifiedResourceSummary {
  id: string;
  source_system: string;
  source_id: string;
  source_label: string;
  title: string;
  resource_type: string;
  profile_key?: string | null;
  profile_label?: string | null;
  status: string;
  preview_enabled: boolean;
  manifest_url: string;
  detail_url: string;
  thumbnail_url?: string | null;
  preview_data?: ThreeDPreviewData | null;
  updated_at: string;
  actions?: UnifiedResourceAction[];
  resolution?: string | null;
  format?: string | null;
  era?: string | null;
  object_level?: string | null;
  main_person?: string | null;
  main_location?: string | null;
}

export interface ThreeDPreviewData {
  kind: string;
  status?: string;
  frame_count?: number;
  poster_url?: string | null;
  frames?: string[];
  source?: string;
  note?: string;
  model_filename?: string | null;
}

export interface UnifiedResourceDetail extends UnifiedResourceSummary {
  source_detail_url: string;
  source_record_type?: 'asset_detail' | 'three_d_detail' | 'three_d_object_detail' | string | null;
  source_record_schema?: string | null;
  source_record?: AssetDetailResponse | ThreeDDetailResponse | ThreeDDigitalObjectDetailResponse | null;
  rights_display?: RightsDisplay | null;
}

export interface PaginatedUnifiedResourceList {
  total: number;
  page: number;
  size: number;
  items: UnifiedResourceSummary[];
}

export interface AdvancedSearchParams {
  q?: string;
  field?: 'title' | 'filename' | 'mime';
  field_value?: string;
  date_from?: string;
  date_to?: string;
  status?: string;
  resource_type?: string;
  profile_key?: string;
  preview_enabled?: string;
  source_system?: string;
}

export interface ThreeDAssetSummary {
  id: number;
  three_d_object_id: number;
  collection_object_id?: number | null;
  resource_group?: string | null;
  filename: string;
  title?: string | null;
  file_size: number;
  mime_type?: string | null;
  file_count?: number;
  primary_file_role?: string | null;
  file_roles?: string[];
  version_label?: string;
  representation_type?: string;
  publication_status?: string;
  version_order?: number;
  is_current?: boolean;
  is_web_preview?: boolean;
  web_preview_status?: string;
  web_preview_reason?: string | null;
  status: string;
  resource_type: string;
  profile_key?: string | null;
  profile_label?: string | null;
  object_number?: string | null;
  object_name?: string | null;
  collection_unit?: string | null;
  storage_tier?: string;
  preservation_status?: string;
  preservation_note?: string | null;
  fixity_status?: string;
  preview_data?: ThreeDPreviewData | null;
  created_at: string;
  process_message?: string | null;
}

export interface ThreeDCollectionObjectSummary {
  id: number;
  object_number?: string | null;
  object_name?: string | null;
  object_type?: string | null;
  collection_unit?: string | null;
  summary?: string | null;
  keywords?: string | null;
}

export interface ThreeDMetadataLayers {
  schema_version?: string;
  core?: Record<string, unknown>;
  management?: Record<string, unknown>;
  collection?: Record<string, unknown>;
  technical?: Record<string, unknown>;
  profile?: {
    key?: string;
    label?: string;
    sheet?: string;
    fields?: Record<string, unknown>;
  };
  preservation?: Record<string, unknown>;
  raw_metadata?: Record<string, unknown>;
}

export interface ThreeDDetailResponse {
  id: number;
  three_d_object_id: number;
  identifier: string;
  title: string;
  resource_type: string;
  resource_type_label: string;
  profile_key?: string | null;
  profile_label?: string | null;
  status: string;
  process_message?: string | null;
  created_at: string;
  file: {
    filename: string;
    file_path: string;
    actual_filename: string;
    file_size: number;
    mime_type?: string | null;
  };
  structure: {
    summary: string;
    primary_file: {
      id?: number | null;
      role: string;
      role_label: string;
      filename: string;
      actual_filename: string;
      file_path: string;
      file_size: number;
      mime_type?: string | null;
      is_primary?: boolean;
      sort_order?: number;
      download_url?: string | null;
      preview_url?: string | null;
      sha256?: string | null;
      fixity_status?: string | null;
      last_verified_at?: string | null;
    };
    files: Array<{
      id?: number | null;
      role: string;
      role_label: string;
      filename: string;
      actual_filename: string;
      file_path: string;
      file_size: number;
      mime_type?: string | null;
      is_primary?: boolean;
      sort_order?: number;
      download_url?: string | null;
      preview_url?: string | null;
      sha256?: string | null;
      fixity_status?: string | null;
      last_verified_at?: string | null;
    }>;
    groups: Array<{
      role: string;
      role_label: string;
      file_count: number;
      total_file_size: number;
    }>;
    packaging?: {
      file_count: number;
      manifest_url?: string | null;
      download_zip_url?: string | null;
      note?: string | null;
    } | null;
  };
  metadata_layers: ThreeDMetadataLayers;
  access: {
    preview_enabled: boolean;
    preview_note?: string | null;
  };
  outputs: {
    download_url: string;
  };
  technical_metadata: Record<string, unknown>;
  viewer?: {
    enabled: boolean;
    reason?: string | null;
    renderer?: string;
    preview_file?: {
      id?: number | null;
      role: string;
      role_label: string;
      filename: string;
      actual_filename: string;
      file_path: string;
      file_size: number;
      mime_type?: string | null;
      is_primary?: boolean;
      sort_order?: number;
      download_url?: string | null;
      preview_url?: string | null;
    } | null;
    preview_url?: string | null;
    supported_roles?: string[];
  } | null;
  version_label?: string;
  representation_type?: string;
  publication_status?: string;
  version_order?: number;
  is_current?: boolean;
  is_web_preview?: boolean;
  web_preview_status?: string;
  web_preview_reason?: string | null;
  resource_group?: string | null;
  collection_object?: {
    id: number;
    object_number?: string | null;
    object_name?: string | null;
    object_type?: string | null;
    collection_unit?: string | null;
    summary?: string | null;
    keywords?: string | null;
  } | null;
  preservation: {
    storage_tier: string;
    preservation_status: string;
    preservation_note?: string | null;
  };
  production_records: Array<{
    id: number;
    stage: string;
    event_type: string;
    status: string;
    actor?: string | null;
    description?: string | null;
    evidence?: string | null;
    occurred_at: string;
    metadata_info?: Record<string, unknown>;
  }>;
  publication_transitions: string[];
}

export interface ThreeDRepresentationSummary {
  id: number;
  source_id: string;
  title: string;
  representation_type: string;
  representation_label: string;
  version_label: string;
  version_order: number;
  is_current: boolean;
  is_web_preview: boolean;
  web_preview_status: string;
  preview_enabled: boolean;
  file_count: number;
  file_groups?: Array<{
    role: string;
    role_label: string;
    file_count: number;
    total_file_size: number;
  }>;
  download_url?: string | null;
  detail_url?: string | null;
  viewer?: ThreeDDetailResponse['viewer'] | null;
  preservation?: {
    storage_tier: string;
    preservation_status: string;
    preservation_note?: string | null;
  };
}

export interface ThreeDFileRecord {
  id: number | null;
  filename: string;
  file_path: string;
  actual_filename: string;
  file_size: number;
  mime_type: string | null;
  role: string;
  role_label: string;
  is_primary: boolean;
  sort_order: number;
  download_url: string | null;
  preview_url: string | null;
}

export interface ThreeDDigitalObjectDetailResponse {
  id: string;
  title: string;
  resource_type: string;
  source_record_schema?: string | null;
  collection_object?: {
    id: number;
    object_number?: string | null;
    object_name?: string | null;
    object_type?: string | null;
    collection_unit?: string | null;
    summary?: string | null;
    keywords?: string | null;
  } | null;
  structure: {
    summary: string;
    representation_count: number;
    file_count: number;
  };
  default_preview_representation_id?: number | null;
  default_preview?: ThreeDDetailResponse | null;
  preview_data?: ThreeDPreviewData | null;
  representations: ThreeDRepresentationSummary[];
}

export interface AssetDetailTimelineItem extends TimelineEntry {
  label?: string;
  description?: string;
}

export interface AssetDetailFileRecord extends FileRecord {
  actual_filename?: string;
}

export interface ThreeDObjectGroup {
  key: string;
  label: string;
  versions: ThreeDAssetSummary[];
  resourceType: string;
  profileLabel: string | null;
  objectNumber: string | null;
  objectName: string | null;
  currentVersion: ThreeDAssetSummary | null;
  webPreviewVersion: ThreeDAssetSummary | null;
  latestVersion: ThreeDAssetSummary | null;
  storageTier: string | null;
  preservationStatus: string | null;
  updatedAt: string | null;
  readyCount: number;
  totalFileCount: number;
}

// ── Import Dialog types ──────────────────────────────────────────────

/** 单个图片项，来自文物号查询返回 */
export interface LookupImageItem {
  sourceSystem: string;
  sourceId: string;
  title: string;
  thumbnailUrl?: string | null;
  manifestUrl?: string | null;
  objectNumber?: string | null;
  /** 分辨率字符串，如 "6000x4000" */
  resolution?: string | null;
  /** 拍摄日期 */
  captureDate?: string | null;
  /** 摄影者 */
  photographer?: string | null;
  /** 拍摄内容 */
  content?: string | null;
  fileSize?: number | null;
  mimeType?: string | null;
}

/** 文物号查询 API 响应 */
export interface LookupResponse {
  items: LookupImageItem[];
  total: number;
  objectNumber: string;
  objectName?: string | null;
}

/** 解析后的导入行（来自文本粘贴或 CSV/Excel） */
export interface ParsedImportRow {
  /** 文物号 */
  objectNumber: string;
  /** 图片ID（如有则为精确匹配） */
  imageId?: string | null;
  /** 拍摄内容 */
  content?: string | null;
  /** 拍摄时间 */
  captureDate?: string | null;
  /** 摄影者 */
  photographer?: string | null;
  /** 匹配类型 */
  matchType: 'exact' | 'expand';
  /** 行号（用于错误定位） */
  lineNo: number;
  /** 原始行文本 */
  raw: string;
}

/** ImportDialog 最终选择导入的条目 */
export interface ImportSelectionItem {
  sourceSystem: string;
  sourceId: string;
  title: string;
  objectNumber?: string | null;
  thumbnailUrl?: string | null;
  manifestUrl?: string | null;
  note?: string | null;
}
