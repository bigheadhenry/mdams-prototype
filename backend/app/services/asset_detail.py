from __future__ import annotations

import os
from collections.abc import Iterable

from app.models import Asset
from app.schemas import (
    AssetAccessPaths,
    AssetAccessSummary,
    AssetDetailResponse,
    AssetFileRecord,
    AssetFileSummary,
    AssetLifecycleEntry,
    AssetManifestLink,
    AssetMiradorPreviewLink,
    AssetOutputActions,
    AssetOutputLink,
    AssetOutputs,
    AssetPackagingInfo,
    AssetStatusInfo,
    AssetStructureResponse,
    AssetTimelineEntry,
)
from .metadata_layers import RESOURCE_TYPE_LABELS, get_metadata_layers

STATUS_LABELS = {
    "processing": "处理中",
    "ready": "可预览",
    "error": "异常",
}

TIMELINE_STATUS_LABELS = {
    "done": "已完成",
    "pending": "处理中",
    "error": "异常",
}


def _has_any_value(metadata: dict[str, object], keys: Iterable[str]) -> bool:
    return any(metadata.get(key) not in (None, "") for key in keys)


def _build_file_record(
    *,
    role: str,
    role_label: str,
    filename: str,
    file_path: str | None,
    mime_type: str | None,
    file_size: int | None,
    is_current: bool | None = None,
    is_original: bool | None = None,
    same_as_primary: bool | None = None,
    derivation_method: str | None = None,
) -> AssetFileRecord:
    return AssetFileRecord(
        role=role,
        role_label=role_label,
        filename=filename,
        file_path=file_path,
        mime_type=mime_type,
        file_size=file_size,
        is_current=is_current,
        is_original=is_original,
        same_as_primary=same_as_primary,
        derivation_method=derivation_method,
    )


def _build_lifecycle_events(
    *,
    asset: Asset,
    metadata: dict[str, object],
    actual_filename: str,
    preview_ready: bool,
    has_fixity: bool,
    has_basic_metadata: bool,
    access_copy_ready: bool,
    has_distinct_original: bool,
) -> list[AssetLifecycleEntry]:
    base_status = "done" if asset.status == "ready" else "pending"
    preview_status = "done" if preview_ready else ("error" if asset.status == "error" else "pending")
    access_status = "done" if access_copy_ready else "pending"

    events = [
        AssetLifecycleEntry(
            step="object_created",
            label="对象创建",
            status="done",
            status_label=TIMELINE_STATUS_LABELS["done"],
            description=f"对象记录已创建，资源编号为 asset-{asset.id}。",
            timestamp=asset.created_at,
            evidence=f"asset.id={asset.id}",
        ),
        AssetLifecycleEntry(
            step="ingest_completed",
            label="入库完成",
            status=base_status,
            status_label=TIMELINE_STATUS_LABELS[base_status],
            description=(
                f"对象已通过 {metadata.get('ingest_method')} 完成入库。"
                if metadata.get("ingest_method")
                else "对象已完成基础入库。"
            ),
            timestamp=asset.created_at,
            evidence=str(metadata.get("ingest_method") or "file_upload"),
        ),
        AssetLifecycleEntry(
            step="fixity_recorded",
            label="Fixity 记录",
            status="done" if has_fixity else "pending",
            status_label=TIMELINE_STATUS_LABELS["done" if has_fixity else "pending"],
            description="已记录 SHA256 fixity。" if has_fixity else "当前对象尚未提供 fixity 信息。",
            timestamp=asset.created_at if has_fixity else None,
            evidence=str(metadata.get("fixity_sha256") or ""),
        ),
        AssetLifecycleEntry(
            step="metadata_extracted",
            label="元数据提取",
            status="done" if has_basic_metadata else "pending",
            status_label=TIMELINE_STATUS_LABELS["done" if has_basic_metadata else "pending"],
            description="已提取尺寸或转换信息。" if has_basic_metadata else "当前对象暂未形成足够的技术元数据。",
            timestamp=asset.created_at if has_basic_metadata else None,
            evidence=";".join(
                key for key in ["width", "height", "original_file_path", "conversion_method", "ingest_method"]
                if metadata.get(key) not in (None, "")
            )
            or None,
        ),
        AssetLifecycleEntry(
            step="access_copy_ready",
            label="访问文件就绪",
            status=access_status,
            status_label=TIMELINE_STATUS_LABELS[access_status],
            description=(
                f"当前访问文件 {actual_filename} 已可直接下载或用于预览。"
                if access_copy_ready
                else "当前访问文件尚未就绪。"
            ),
            timestamp=asset.created_at if access_copy_ready else None,
            evidence=actual_filename,
        ),
        AssetLifecycleEntry(
            step="preview_ready",
            label="预览就绪",
            status=preview_status,
            status_label=TIMELINE_STATUS_LABELS[preview_status],
            description=(
                "对象已经可以通过 IIIF / Mirador 访问。"
                if preview_ready
                else ("对象处理异常，预览不可用。" if asset.status == "error" else "对象仍在处理中，预览尚未开放。")
            ),
            timestamp=asset.created_at if preview_ready else None,
            evidence=f"/api/iiif/{asset.id}/manifest",
        ),
        AssetLifecycleEntry(
            step="output_ready",
            label="输出就绪",
            status="done" if access_copy_ready else "pending",
            status_label=TIMELINE_STATUS_LABELS["done" if access_copy_ready else "pending"],
            description="当前文件下载和 BagIt 输出入口已开放。" if access_copy_ready else "当前对象的输出入口尚未完全开放。",
            timestamp=asset.created_at if access_copy_ready else None,
            evidence=f"/api/assets/{asset.id}/download",
        ),
    ]

    if has_distinct_original:
        events.insert(
            5,
            AssetLifecycleEntry(
                step="derived_master_ready",
                label="转换后主文件就绪",
                status="done" if access_copy_ready else "pending",
                status_label=TIMELINE_STATUS_LABELS["done" if access_copy_ready else "pending"],
                description="当前对象保留了独立的转换后主文件。",
                timestamp=asset.created_at if access_copy_ready else None,
                evidence=actual_filename,
            ),
        )

    return events


def build_asset_detail_response(asset: Asset) -> AssetDetailResponse:
    metadata_layers = get_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_visibility_scope=asset.visibility_scope,
        asset_collection_object_id=asset.collection_object_id,
        asset_created_at=asset.created_at,
        metadata=asset.metadata_info or {},
    )
    technical = metadata_layers["technical"]
    actual_filename = os.path.basename(asset.file_path) if asset.file_path else asset.filename
    original_file_path = technical.get("original_file_path")
    has_distinct_original = bool(original_file_path and original_file_path != asset.file_path)
    original_filename = os.path.basename(original_file_path) if has_distinct_original else actual_filename

    status_label = STATUS_LABELS.get(asset.status, asset.status)
    preview_ready = asset.status == "ready"
    has_error = asset.status == "error"

    primary_file = _build_file_record(
        role="primary_file",
        role_label="当前访问文件",
        filename=actual_filename,
        file_path=asset.file_path,
        mime_type=asset.mime_type,
        file_size=asset.file_size,
        is_current=True,
        is_original=not has_distinct_original,
    )

    original_file = _build_file_record(
        role="original_file",
        role_label="原始文件",
        filename=original_filename,
        file_path=original_file_path if has_distinct_original else asset.file_path,
        mime_type=technical.get("original_mime_type", asset.mime_type),
        file_size=technical.get("original_file_size", asset.file_size),
        is_current=not has_distinct_original,
        is_original=True,
        same_as_primary=not has_distinct_original,
    )

    derivatives: list[AssetFileRecord] = []
    if has_distinct_original:
        derivatives.append(
            _build_file_record(
                role="converted_master",
                role_label="转换后主文件",
                filename=actual_filename,
                file_path=asset.file_path,
                mime_type=asset.mime_type,
                file_size=asset.file_size,
                derivation_method=technical.get("conversion_method"),
            )
        )

    has_fixity = bool(technical.get("fixity_sha256"))
    has_basic_metadata = _has_any_value(
        technical,
        ["width", "height", "original_file_path", "conversion_method", "ingest_method"],
    )
    access_copy_ready = bool(asset.file_path and os.path.exists(asset.file_path))

    structure_summary = "当前对象已形成可访问的单文件资源结构。"
    if has_distinct_original:
        structure_summary = "当前对象同时保留原始文件与当前访问文件，已具备转换后的访问层。"

    lifecycle = _build_lifecycle_events(
        asset=asset,
        metadata=technical,
        actual_filename=actual_filename,
        preview_ready=preview_ready,
        has_fixity=has_fixity,
        has_basic_metadata=has_basic_metadata,
        access_copy_ready=access_copy_ready,
        has_distinct_original=has_distinct_original,
    )

    process_timeline = [
        AssetTimelineEntry(step=item.step, label=item.label, status=item.status, status_label=item.status_label, description=item.description)
        for item in lifecycle
    ]

    return AssetDetailResponse(
        id=asset.id,
        identifier=f"asset-{asset.id}",
        title=str(metadata_layers["core"].get("title") or asset.filename),
        resource_type=asset.resource_type or "image_2d_cultural_object",
        resource_type_label=RESOURCE_TYPE_LABELS.get(asset.resource_type or "", "二维图像文物资源"),
        visibility_scope=str(asset.visibility_scope or metadata_layers["core"].get("visibility_scope") or "open"),
        collection_object_id=asset.collection_object_id,
        status=asset.status,
        process_message=asset.process_message,
        created_at=asset.created_at,
        file=AssetFileSummary(
            filename=asset.filename,
            file_path=asset.file_path,
            actual_filename=actual_filename,
            file_size=asset.file_size,
            mime_type=asset.mime_type,
        ),
        status_info=AssetStatusInfo(
            code=asset.status,
            label=status_label,
            message=asset.process_message,
            preview_ready=preview_ready,
            has_error=has_error,
        ),
        lifecycle=lifecycle,
        process_timeline=process_timeline,
        structure=AssetStructureResponse(
            summary=structure_summary,
            primary_file=primary_file,
            original_file=original_file,
            derivatives=derivatives,
            packaging=AssetPackagingInfo(
                bagit_supported=True,
                bagit_note="BagIt 打包用于归档和下载，保留当前对象的可移植副本。",
            ),
        ),
        technical_metadata=technical,
        metadata_layers=metadata_layers,
        access=AssetAccessSummary(
            manifest_url=f"/api/iiif/{asset.id}/manifest",
            preview_enabled=preview_ready,
        ),
        access_paths=AssetAccessPaths(
            manifest=AssetManifestLink(
                label="IIIF Manifest",
                url=f"/api/iiif/{asset.id}/manifest",
            ),
            mirador_preview=AssetMiradorPreviewLink(
                label="Mirador 预览",
                manifest_url=f"/api/iiif/{asset.id}/manifest",
                enabled=preview_ready,
            ),
            preview_enabled=preview_ready,
        ),
        outputs=AssetOutputs(
            download_url=f"/api/assets/{asset.id}/download",
            download_bag_url=f"/api/assets/{asset.id}/download-bag",
        ),
        output_actions=AssetOutputActions(
            download_current_file=AssetOutputLink(
                label="下载当前文件",
                url=f"/api/assets/{asset.id}/download",
            ),
            download_bag=AssetOutputLink(
                label="下载 BagIt 包",
                url=f"/api/assets/{asset.id}/download-bag",
            ),
        ),
    )
