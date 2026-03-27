export interface AssetSummary {
  id: number;
  filename: string;
  file_size: number;
  mime_type: string;
  status: string;
  created_at: string;
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
  created_at: string;
  process_message?: string | null;
}

export interface ThreeDMetadataLayers {
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
  version_label?: string;
  version_order?: number;
  is_current?: boolean;
  is_web_preview?: boolean;
  web_preview_status?: string;
  web_preview_reason?: string | null;
  resource_group?: string | null;
}

export interface AssetDetailTimelineItem extends TimelineEntry {
  label?: string;
  description?: string;
}

export interface AssetDetailFileRecord extends FileRecord {
  actual_filename?: string;
}
