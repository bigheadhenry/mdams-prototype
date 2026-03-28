from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AssetOut(BaseModel):
    id: int
    filename: str
    file_path: str
    file_size: int
    mime_type: str
    created_at: datetime
    status: str
    resource_type: str | None = None
    process_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AssetFileRecord(BaseModel):
    role: str | None = None
    role_label: str | None = None
    filename: str | None = None
    file_path: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    actual_filename: str | None = None
    is_current: bool | None = None
    is_original: bool | None = None
    same_as_primary: bool | None = None
    derivation_method: str | None = None


class AssetLifecycleEntry(BaseModel):
    step: str
    label: str
    status: str
    status_label: str
    description: str
    timestamp: datetime | None = None
    evidence: str | None = None


class AssetTimelineEntry(BaseModel):
    step: str | None = None
    label: str | None = None
    status: str | None = None
    status_label: str | None = None
    description: str | None = None


class AssetFileSummary(BaseModel):
    filename: str
    file_path: str
    actual_filename: str
    file_size: int
    mime_type: str | None = None


class AssetStatusInfo(BaseModel):
    code: str
    label: str
    message: str | None = None
    preview_ready: bool
    has_error: bool


class AssetManifestLink(BaseModel):
    label: str | None = None
    url: str | None = None


class AssetMiradorPreviewLink(BaseModel):
    label: str | None = None
    manifest_url: str | None = None
    enabled: bool | None = None


class AssetAccessPaths(BaseModel):
    manifest: AssetManifestLink | None = None
    mirador_preview: AssetMiradorPreviewLink | None = None
    preview_enabled: bool | None = None


class AssetOutputLink(BaseModel):
    label: str | None = None
    url: str | None = None


class AssetOutputs(BaseModel):
    download_url: str
    download_bag_url: str


class AssetOutputActions(BaseModel):
    download_current_file: AssetOutputLink | None = None
    download_bag: AssetOutputLink | None = None


class AssetPackagingInfo(BaseModel):
    bagit_supported: bool | None = None
    bagit_note: str | None = None


class AssetAccessSummary(BaseModel):
    manifest_url: str
    preview_enabled: bool


class AssetStructureResponse(BaseModel):
    summary: str
    primary_file: AssetFileRecord
    original_file: AssetFileRecord
    derivatives: list[AssetFileRecord]
    packaging: AssetPackagingInfo | None = None


class AssetDetailResponse(BaseModel):
    id: int
    identifier: str
    title: str
    resource_type: str
    resource_type_label: str
    status: str
    process_message: str | None = None
    created_at: datetime
    file: AssetFileSummary
    status_info: AssetStatusInfo
    lifecycle: list[AssetLifecycleEntry]
    process_timeline: list[AssetTimelineEntry]
    structure: AssetStructureResponse
    technical_metadata: dict[str, Any]
    metadata_layers: dict[str, Any]
    access: AssetAccessSummary
    access_paths: AssetAccessPaths
    outputs: AssetOutputs
    output_actions: AssetOutputActions

    model_config = ConfigDict(from_attributes=True)


class UnifiedResourceSourceSummary(BaseModel):
    source_system: str
    source_label: str
    resource_type: str
    resource_count: int
    status: str
    healthy: bool
    last_synced_at: datetime | None = None
    entrypoint: str


class UnifiedResourceSummary(BaseModel):
    id: str
    source_system: str
    source_id: str
    source_label: str
    title: str
    resource_type: str
    profile_key: str | None = None
    profile_label: str | None = None
    status: str
    preview_enabled: bool
    manifest_url: str
    detail_url: str
    updated_at: datetime


class UnifiedResourceDetail(UnifiedResourceSummary):
    source_detail_url: str
    source_record: AssetDetailResponse | None = None


class IngestSipResponse(BaseModel):
    status: str
    message: str
    asset_id: int
    fixity_check: str
    sha256: str


class ApplicationCreateItemRequest(BaseModel):
    asset_id: int
    requested_variant: str | None = "current"
    delivery_format: str | None = "image"
    note: str | None = None


class ApplicationCreateRequest(BaseModel):
    requester_name: str
    requester_org: str | None = None
    contact_email: str | None = None
    purpose: str
    usage_scope: str | None = None
    items: list[ApplicationCreateItemRequest] = Field(default_factory=list)


class ApplicationApproveRequest(BaseModel):
    review_note: str | None = None


class ApplicationAssetRef(BaseModel):
    id: int
    filename: str
    resource_type: str | None = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class ApplicationItemResponse(BaseModel):
    id: int
    asset_id: int
    requested_variant: str | None = None
    delivery_format: str | None = None
    note: str | None = None
    created_at: datetime
    asset: ApplicationAssetRef

    model_config = ConfigDict(from_attributes=True)


class ApplicationListItem(BaseModel):
    id: int
    application_no: str
    requester_name: str
    requester_org: str | None = None
    purpose: str
    usage_scope: str | None = None
    status: str
    status_label: str
    review_note: str | None = None
    item_count: int
    created_at: datetime
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None


class ApplicationDetailResponse(BaseModel):
    id: int
    application_no: str
    requester_name: str
    requester_org: str | None = None
    contact_email: str | None = None
    purpose: str
    usage_scope: str | None = None
    status: str
    review_note: str | None = None
    created_at: datetime
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    items: list[ApplicationItemResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ThreeDCollectionObjectOut(BaseModel):
    id: int
    object_number: str | None = None
    object_name: str | None = None
    object_type: str | None = None
    collection_unit: str | None = None
    summary: str | None = None
    keywords: str | None = None


class ThreeDProductionRecordOut(BaseModel):
    id: int
    stage: str
    event_type: str
    status: str
    actor: str | None = None
    description: str | None = None
    evidence: str | None = None
    occurred_at: datetime
    metadata_info: dict[str, Any] = Field(default_factory=dict)


class ThreeDPreservationSummary(BaseModel):
    storage_tier: str
    preservation_status: str
    preservation_note: str | None = None


class ThreeDAssetOut(BaseModel):
    id: int
    collection_object_id: int | None = None
    resource_group: str | None = None
    filename: str
    title: str | None = None
    file_size: int
    mime_type: str | None = None
    file_count: int = 0
    primary_file_role: str | None = None
    file_roles: list[str] = Field(default_factory=list)
    version_label: str = "original"
    version_order: int = 0
    is_current: bool = True
    is_web_preview: bool = False
    web_preview_status: str = "disabled"
    web_preview_reason: str | None = None
    status: str
    resource_type: str
    profile_key: str | None = None
    profile_label: str | None = None
    object_number: str | None = None
    object_name: str | None = None
    collection_unit: str | None = None
    storage_tier: str = "archive"
    preservation_status: str = "pending"
    preservation_note: str | None = None
    created_at: datetime
    process_message: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ThreeDFileSummary(BaseModel):
    filename: str
    file_path: str
    actual_filename: str
    file_size: int
    mime_type: str | None = None


class ThreeDFileRecord(ThreeDFileSummary):
    id: int | None = None
    role: str
    role_label: str
    is_primary: bool = False
    sort_order: int = 0
    download_url: str | None = None
    preview_url: str | None = None


class ThreeDFileGroupSummary(BaseModel):
    role: str
    role_label: str
    file_count: int
    total_file_size: int


class ThreeDPackagingInfo(BaseModel):
    file_count: int
    manifest_url: str | None = None
    download_zip_url: str | None = None
    note: str | None = None


class ThreeDStructureResponse(BaseModel):
    summary: str
    primary_file: ThreeDFileRecord
    files: list[ThreeDFileRecord]
    groups: list[ThreeDFileGroupSummary]
    packaging: ThreeDPackagingInfo | None = None


class ThreeDAccessSummary(BaseModel):
    preview_enabled: bool
    preview_note: str | None = None


class ThreeDOutputs(BaseModel):
    download_url: str


class ThreeDViewerSummary(BaseModel):
    enabled: bool
    reason: str | None = None
    renderer: str = "model-viewer"
    preview_file: ThreeDFileRecord | None = None
    preview_url: str | None = None
    supported_roles: list[str] = Field(default_factory=lambda: ["model"])


class ThreeDDetailResponse(BaseModel):
    id: int
    identifier: str
    title: str
    resource_type: str
    resource_type_label: str
    profile_key: str | None = None
    profile_label: str | None = None
    status: str
    process_message: str | None = None
    created_at: datetime
    file: ThreeDFileSummary
    structure: ThreeDStructureResponse
    metadata_layers: dict[str, Any]
    access: ThreeDAccessSummary
    outputs: ThreeDOutputs
    technical_metadata: dict[str, Any]
    viewer: ThreeDViewerSummary | None = None
    version_label: str = "original"
    version_order: int = 0
    is_current: bool = True
    is_web_preview: bool = False
    web_preview_status: str = "disabled"
    web_preview_reason: str | None = None
    resource_group: str | None = None
    collection_object: ThreeDCollectionObjectOut | None = None
    preservation: ThreeDPreservationSummary
    production_records: list[ThreeDProductionRecordOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ThreeDMetadataFieldDefinition(BaseModel):
    key: str
    label: str
    required: bool = False
    layer: str
    description: str | None = None


class ThreeDMetadataDictionarySection(BaseModel):
    key: str
    label: str
    fields: list[ThreeDMetadataFieldDefinition] = Field(default_factory=list)


class ThreeDMetadataDictionaryResponse(BaseModel):
    schema_version: str
    sections: list[ThreeDMetadataDictionarySection] = Field(default_factory=list)
