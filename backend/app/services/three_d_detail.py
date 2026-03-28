from __future__ import annotations

import os
from typing import Any

from ..models import ThreeDAsset
from ..schemas import (
    ThreeDAccessSummary,
    ThreeDCollectionObjectOut,
    ThreeDDetailResponse,
    ThreeDFileGroupSummary,
    ThreeDFileRecord,
    ThreeDFileSummary,
    ThreeDOutputs,
    ThreeDPackagingInfo,
    ThreeDProductionRecordOut,
    ThreeDPreservationSummary,
    ThreeDViewerSummary,
    ThreeDStructureResponse,
)
from .three_d_metadata import RESOURCE_TYPE_LABELS, build_three_d_metadata_layers
from .three_d_storage import summarize_three_d_files


def _to_file_record(record: Any, *, asset_id: int, is_primary: bool = False) -> ThreeDFileRecord:
    file_id = getattr(record, 'id', None)
    return ThreeDFileRecord(
        id=file_id,
        role=str(getattr(record, 'role', 'other') or 'other'),
        role_label=str(getattr(record, 'role_label', '其他') or '其他'),
        filename=str(getattr(record, 'filename', '') or ''),
        actual_filename=str(getattr(record, 'actual_filename', '') or getattr(record, 'filename', '') or ''),
        file_path=str(getattr(record, 'file_path', '') or ''),
        file_size=int(getattr(record, 'file_size', 0) or 0),
        mime_type=getattr(record, 'mime_type', None),
        is_primary=is_primary or bool(getattr(record, 'is_primary', False)),
        sort_order=int(getattr(record, 'sort_order', 0) or 0),
        download_url=f'/api/three-d/resources/{asset_id}/files/{file_id}' if file_id is not None else None,
        preview_url=f'/api/three-d/resources/{asset_id}/files/{file_id}' if file_id is not None else None,
    )


def _to_production_record_out(record: Any) -> ThreeDProductionRecordOut:
    return ThreeDProductionRecordOut(
        id=int(getattr(record, 'id', 0) or 0),
        stage=str(getattr(record, 'stage', 'other') or 'other'),
        event_type=str(getattr(record, 'event_type', 'unknown') or 'unknown'),
        status=str(getattr(record, 'status', 'unknown') or 'unknown'),
        actor=getattr(record, 'actor', None),
        description=getattr(record, 'description', None),
        evidence=getattr(record, 'evidence', None),
        occurred_at=getattr(record, 'occurred_at'),
        metadata_info=dict(getattr(record, 'metadata_info', {}) or {}),
    )


def build_three_d_viewer_summary(
    *,
    asset: ThreeDAsset,
    file_records: list[ThreeDFileRecord],
    primary_file: ThreeDFileRecord | None,
) -> ThreeDViewerSummary:
    model_file = next((record for record in file_records if record.role == 'model'), None)
    preview_file = model_file or primary_file
    if preview_file is None:
        return ThreeDViewerSummary(
            enabled=False,
            reason='没有可用于预览的三维文件。',
            preview_file=None,
            preview_url=None,
        )

    if not (asset.is_web_preview and asset.web_preview_status == 'ready'):
        return ThreeDViewerSummary(
            enabled=False,
            reason='当前版本尚未标记为可 Web 展示。',
            preview_file=preview_file,
            preview_url=preview_file.preview_url or preview_file.download_url,
        )

    if preview_file.role != 'model':
        return ThreeDViewerSummary(
            enabled=False,
            reason='当前版本缺少可用于 Web 展示的模型文件。',
            preview_file=preview_file,
            preview_url=preview_file.preview_url or preview_file.download_url,
        )

    return ThreeDViewerSummary(
        enabled=True,
        reason=None,
        preview_file=preview_file,
        preview_url=preview_file.preview_url or preview_file.download_url,
    )


def build_three_d_detail_response(asset: ThreeDAsset) -> ThreeDDetailResponse:
    saved_files = list(asset.files or [])
    file_records = [_to_file_record(file_record, asset_id=asset.id) for file_record in saved_files]
    primary_file = next((record for record in file_records if record.is_primary), None) or (file_records[0] if file_records else None)

    metadata_layers = build_three_d_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_created_at=asset.created_at,
        metadata=asset.metadata_info or {},
        file_records=[record.model_dump() for record in file_records],
    )
    technical = metadata_layers['technical']
    actual_filename = os.path.basename(asset.file_path) if asset.file_path else asset.filename

    groups, role_summary = summarize_three_d_files([record.model_dump() for record in file_records])

    if primary_file is None:
        primary_file = ThreeDFileRecord(
            role='other',
            role_label='其他',
            filename=asset.filename,
            actual_filename=actual_filename,
            file_path=asset.file_path,
            file_size=asset.file_size,
            mime_type=asset.mime_type,
            is_primary=True,
        )

    summary_text = role_summary if role_summary != '暂无文件' else '暂无文件'
    viewer = build_three_d_viewer_summary(asset=asset, file_records=file_records, primary_file=primary_file)

    return ThreeDDetailResponse(
        id=asset.id,
        identifier=f'three-d-{asset.id}',
        title=str(metadata_layers['core'].get('title') or asset.filename),
        resource_type=asset.resource_type or 'three_d_model',
        resource_type_label=RESOURCE_TYPE_LABELS.get(asset.resource_type or '', '三维资源'),
        profile_key=str(metadata_layers['core'].get('profile_key') or 'other'),
        profile_label=str(metadata_layers['core'].get('profile_label') or '其他'),
        status=asset.status,
        process_message=asset.process_message,
        created_at=asset.created_at,
        file=ThreeDFileSummary(
            filename=primary_file.filename,
            file_path=primary_file.file_path,
            actual_filename=primary_file.actual_filename,
            file_size=primary_file.file_size,
            mime_type=primary_file.mime_type,
        ),
        structure=ThreeDStructureResponse(
            summary=summary_text,
            primary_file=primary_file,
            files=file_records,
            groups=[ThreeDFileGroupSummary(**group) for group in groups],
            packaging=ThreeDPackagingInfo(
                file_count=len(file_records),
                manifest_url=f'/api/three-d/resources/{asset.id}',
                download_zip_url=f'/api/three-d/resources/{asset.id}/download',
                note='三维资源按文件组保存，下载时会自动打包为压缩包。',
            ),
        ),
        collection_object=ThreeDCollectionObjectOut(
            id=asset.collection_object.id,
            object_number=asset.collection_object.object_number,
            object_name=asset.collection_object.object_name,
            object_type=asset.collection_object.object_type,
            collection_unit=asset.collection_object.collection_unit,
            summary=asset.collection_object.summary,
            keywords=asset.collection_object.keywords,
        ) if asset.collection_object else None,
        preservation=ThreeDPreservationSummary(
            storage_tier=asset.storage_tier or 'archive',
            preservation_status=asset.preservation_status or 'pending',
            preservation_note=asset.preservation_note,
        ),
        production_records=[_to_production_record_out(record) for record in asset.production_records],
        metadata_layers=metadata_layers,
        access=ThreeDAccessSummary(
            preview_enabled=bool(asset.is_web_preview and asset.web_preview_status == 'ready'),
            preview_note=(
                '当前版本可用于 Web 展示。'
                if asset.is_web_preview and asset.web_preview_status == 'ready'
                else '当前版本未开放 Web 预览，可通过下载或查看文件结构浏览资源。'
            ),
        ),
        outputs=ThreeDOutputs(
            download_url=f'/api/three-d/resources/{asset.id}/download',
        ),
        technical_metadata=technical,
        viewer=viewer,
        version_label=asset.version_label or 'original',
        version_order=asset.version_order or 0,
        is_current=bool(asset.is_current),
        is_web_preview=bool(asset.is_web_preview),
        web_preview_status=asset.web_preview_status or 'disabled',
        web_preview_reason=asset.web_preview_reason,
        resource_group=asset.resource_group,
    )
