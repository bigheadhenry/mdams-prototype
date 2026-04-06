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
from .iiif_access import (
    get_asset_iiif_access_file_path,
    get_asset_iiif_access_mime_type,
    get_asset_original_file_path,
    get_asset_primary_file_path,
    is_iiif_ready,
)
from .metadata_layers import RESOURCE_TYPE_LABELS, get_metadata_layers

STATUS_LABELS = {
    "processing": "Processing",
    "ready": "Ready",
    "error": "Error",
}

TIMELINE_STATUS_LABELS = {
    "done": "Done",
    "pending": "Pending",
    "error": "Error",
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
    technical: dict[str, object],
    preview_ready: bool,
    has_fixity: bool,
    has_basic_metadata: bool,
    access_copy_ready: bool,
    has_distinct_access_copy: bool,
) -> list[AssetLifecycleEntry]:
    base_status = "done" if asset.status == "ready" else ("error" if asset.status == "error" else "pending")
    preview_status = "done" if preview_ready else ("error" if asset.status == "error" else "pending")
    access_status = "done" if access_copy_ready else ("error" if asset.status == "error" else "pending")

    events = [
        AssetLifecycleEntry(
            step="object_created",
            label="Object Created",
            status="done",
            status_label=TIMELINE_STATUS_LABELS["done"],
            description=f"Asset record asset-{asset.id} has been created.",
            timestamp=asset.created_at,
            evidence=f"asset.id={asset.id}",
        ),
        AssetLifecycleEntry(
            step="ingest_completed",
            label="Ingest Completed",
            status=base_status,
            status_label=TIMELINE_STATUS_LABELS[base_status],
            description=(
                f"Asset ingest completed via {technical.get('ingest_method')}."
                if technical.get("ingest_method")
                else "Asset ingest has been recorded."
            ),
            timestamp=asset.created_at,
            evidence=str(technical.get("ingest_method") or "file_upload"),
        ),
        AssetLifecycleEntry(
            step="fixity_recorded",
            label="Fixity Recorded",
            status="done" if has_fixity else "pending",
            status_label=TIMELINE_STATUS_LABELS["done" if has_fixity else "pending"],
            description="SHA256 fixity metadata is present." if has_fixity else "SHA256 fixity metadata has not been recorded yet.",
            timestamp=asset.created_at if has_fixity else None,
            evidence=str(technical.get("fixity_sha256") or ""),
        ),
        AssetLifecycleEntry(
            step="metadata_extracted",
            label="Metadata Extracted",
            status="done" if has_basic_metadata else "pending",
            status_label=TIMELINE_STATUS_LABELS["done" if has_basic_metadata else "pending"],
            description="Technical image metadata has been extracted." if has_basic_metadata else "Technical metadata is still incomplete.",
            timestamp=asset.created_at if has_basic_metadata else None,
            evidence=";".join(
                key for key in ["width", "height", "original_file_path", "conversion_method", "ingest_method"]
                if technical.get(key) not in (None, "")
            ) or None,
        ),
        AssetLifecycleEntry(
            step="iiif_access_ready",
            label="IIIF Access Ready",
            status=access_status,
            status_label=TIMELINE_STATUS_LABELS[access_status],
            description=(
                "IIIF access source is available for Mirador delivery."
                if access_copy_ready
                else "IIIF access source is not ready yet."
            ),
            timestamp=asset.created_at if access_copy_ready else None,
            evidence=str(technical.get("iiif_access_file_path") or technical.get("original_file_path") or ""),
        ),
        AssetLifecycleEntry(
            step="preview_ready",
            label="Mirador Preview Ready",
            status=preview_status,
            status_label=TIMELINE_STATUS_LABELS[preview_status],
            description=(
                "Mirador can open this asset through the IIIF manifest."
                if preview_ready
                else ("IIIF access failed to build." if asset.status == "error" else "Mirador preview is not available yet.")
            ),
            timestamp=asset.created_at if preview_ready else None,
            evidence=f"/api/iiif/{asset.id}/manifest",
        ),
        AssetLifecycleEntry(
            step="output_ready",
            label="Outputs Ready",
            status="done" if access_copy_ready else "pending",
            status_label=TIMELINE_STATUS_LABELS["done" if access_copy_ready else "pending"],
            description="Download endpoints are available." if access_copy_ready else "Download endpoints are waiting on the access source.",
            timestamp=asset.created_at if access_copy_ready else None,
            evidence=f"/api/assets/{asset.id}/download",
        ),
    ]

    if has_distinct_access_copy:
        events.insert(
            5,
            AssetLifecycleEntry(
                step="access_derivative_generated",
                label="Access Derivative Generated",
                status=access_status,
                status_label=TIMELINE_STATUS_LABELS[access_status],
                description="A dedicated IIIF access derivative is tracked separately from the preserved original.",
                timestamp=asset.created_at if access_copy_ready else None,
                evidence=str(technical.get("iiif_access_file_path") or ""),
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

    original_file_path = get_asset_original_file_path(asset)
    iiif_access_file_path = get_asset_iiif_access_file_path(
        asset,
        allow_original_fallback=True,
        require_exists=False,
    )
    primary_file_path = get_asset_primary_file_path(asset, require_exists=False)

    original_filename = os.path.basename(original_file_path) if original_file_path else asset.filename
    primary_filename = os.path.basename(primary_file_path) if primary_file_path else asset.filename

    has_distinct_access_copy = bool(
        iiif_access_file_path
        and original_file_path
        and iiif_access_file_path != original_file_path
    )
    status_label = STATUS_LABELS.get(asset.status, asset.status)
    preview_ready = is_iiif_ready(asset)
    has_error = asset.status == "error"

    primary_file = _build_file_record(
        role="primary_file",
        role_label="Current Access Source",
        filename=primary_filename,
        file_path=primary_file_path,
        mime_type=get_asset_iiif_access_mime_type(asset),
        file_size=os.path.getsize(primary_file_path) if primary_file_path and os.path.exists(primary_file_path) else None,
        is_current=True,
        is_original=not has_distinct_access_copy,
    )

    original_file = _build_file_record(
        role="original_file",
        role_label="Preserved Original",
        filename=original_filename,
        file_path=original_file_path,
        mime_type=str(technical.get("original_mime_type") or asset.mime_type or ""),
        file_size=int(technical.get("original_file_size") or asset.file_size or 0) or None,
        is_current=not has_distinct_access_copy,
        is_original=True,
        same_as_primary=not has_distinct_access_copy,
    )

    derivatives: list[AssetFileRecord] = []
    if has_distinct_access_copy and iiif_access_file_path:
        derivatives.append(
            _build_file_record(
                role="iiif_access_copy",
                role_label="IIIF Access Copy",
                filename=os.path.basename(iiif_access_file_path),
                file_path=iiif_access_file_path,
                mime_type=get_asset_iiif_access_mime_type(asset),
                file_size=os.path.getsize(iiif_access_file_path) if os.path.exists(iiif_access_file_path) else None,
                is_current=True,
                is_original=False,
                derivation_method=str(technical.get("conversion_method") or ""),
            )
        )

    preview_image_path = technical.get("preview_image_path")
    if isinstance(preview_image_path, str) and preview_image_path and preview_image_path not in {
        primary_file_path,
        original_file_path,
        iiif_access_file_path,
    }:
        derivatives.append(
            _build_file_record(
                role="preview_image",
                role_label="Preview Image",
                filename=os.path.basename(preview_image_path),
                file_path=preview_image_path,
                mime_type=str(technical.get("preview_image_mime_type") or "image/jpeg"),
                file_size=os.path.getsize(preview_image_path) if os.path.exists(preview_image_path) else None,
                is_current=False,
                is_original=False,
            )
        )

    has_fixity = bool(technical.get("fixity_sha256"))
    has_basic_metadata = _has_any_value(
        technical,
        ["width", "height", "original_file_path", "conversion_method", "ingest_method"],
    )
    access_copy_ready = bool(primary_file_path and os.path.exists(primary_file_path))

    structure_summary = "The preserved original is also the current IIIF access source."
    if has_distinct_access_copy:
        structure_summary = "The preserved original and the IIIF access derivative are tracked separately."

    lifecycle = _build_lifecycle_events(
        asset=asset,
        technical=technical,
        preview_ready=preview_ready,
        has_fixity=has_fixity,
        has_basic_metadata=has_basic_metadata,
        access_copy_ready=access_copy_ready,
        has_distinct_access_copy=has_distinct_access_copy,
    )

    process_timeline = [
        AssetTimelineEntry(
            step=item.step,
            label=item.label,
            status=item.status,
            status_label=item.status_label,
            description=item.description,
        )
        for item in lifecycle
    ]

    return AssetDetailResponse(
        id=asset.id,
        identifier=f"asset-{asset.id}",
        title=str(metadata_layers["core"].get("title") or asset.filename),
        resource_type=asset.resource_type or "image_2d_cultural_object",
        resource_type_label=RESOURCE_TYPE_LABELS.get(asset.resource_type or "", "2D Cultural Object Image"),
        visibility_scope=str(asset.visibility_scope or metadata_layers["core"].get("visibility_scope") or "open"),
        collection_object_id=asset.collection_object_id,
        status=asset.status,
        process_message=asset.process_message,
        created_at=asset.created_at,
        file=AssetFileSummary(
            filename=asset.filename,
            file_path=asset.file_path,
            actual_filename=original_filename,
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
                bagit_note="BagIt packages include the preserved original and, when present, the IIIF access derivative.",
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
                label="Mirador Preview",
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
                label="Download Current File",
                url=f"/api/assets/{asset.id}/download",
            ),
            download_bag=AssetOutputLink(
                label="Download BagIt Package",
                url=f"/api/assets/{asset.id}/download-bag",
            ),
        ),
    )
