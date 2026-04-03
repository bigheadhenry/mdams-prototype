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

export interface ApplicationCartItem {
  assetId: number;
  resourceId: string;
  title: string;
  manifestUrl: string;
  objectNumber?: string | null;
  sourceLabel?: string | null;
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
  raw_metadata?: Record<string, unknown>;
}

export interface AssetAccessSummary {
  manifest_url: string;
  preview_enabled: boolean;
}

export interface MiradorSearchResult {
  asset_id: number;
  title: string;
  manifest_url: string;
  resource_id: string;
  object_number?: string | null;
  filename?: string | null;
  score?: number;
  reasons?: string[];
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
}

export interface MiradorAIRequest {
  prompt: string;
  current_asset_id?: number | null;
  current_manifest_url?: string | null;
  current_title?: string | null;
  current_object_number?: string | null;
  current_resource_id?: string | null;
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
  updated_at: string;
}

export interface UnifiedResourceDetail extends UnifiedResourceSummary {
  source_detail_url: string;
  source_record?: AssetDetailResponse | null;
}

export interface ThreeDAssetSummary {
  id: number;
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
}

export interface AssetDetailTimelineItem extends TimelineEntry {
  label?: string;
  description?: string;
}

export interface AssetDetailFileRecord extends FileRecord {
  actual_filename?: string;
}
