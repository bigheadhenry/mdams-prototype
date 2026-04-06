from __future__ import annotations

import os
from typing import Any, Mapping

import pyvips
from sqlalchemy.orm.attributes import flag_modified

from .. import config
from ..models import Asset
from .metadata_layers import build_metadata_layers, get_technical_metadata

IIIF_ACCESS_DIR_NAME = "derivatives"
IIIF_ACCESS_FILENAME = "iiif-access.pyramidal.tiff"
IIIF_ACCESS_MIME_TYPE = "image/tiff"
IIIF_TILE_SIZE = 256


def _normalize_path(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _path_exists(path: str | None) -> bool:
    return bool(path) and os.path.exists(path)


def build_asset_layers(asset: Asset) -> dict[str, Any]:
    return build_metadata_layers(
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


def requires_iiif_access_derivative(layers_or_metadata: Mapping[str, Any] | None) -> bool:
    technical = get_technical_metadata(layers_or_metadata)
    strategy = str(technical.get("derivative_strategy") or "").strip().lower()
    priority = str(technical.get("derivative_priority") or "").strip().lower()
    rule_id = str(technical.get("derivative_rule_id") or "").strip().lower()
    source_family = str(technical.get("derivative_source_family") or "").strip().lower()

    if priority == "required":
        return True
    if strategy == "generate_pyramidal_tiff" and source_family in {"psb", "tiff"}:
        return True
    return rule_id in {"psb_mandatory_access_bigtiff", "tiff_large_pyramidal_tiled_copy"}


def populate_iiif_access_metadata(
    layers_or_metadata: Mapping[str, Any] | None,
    *,
    asset_file_path: str | None,
    asset_filename: str | None,
    asset_file_size: int | None,
    asset_mime_type: str | None,
) -> dict[str, Any]:
    layers = build_metadata_layers(
        asset_filename=asset_filename,
        asset_file_path=asset_file_path,
        asset_file_size=asset_file_size,
        asset_mime_type=asset_mime_type,
        metadata=layers_or_metadata,
    )
    technical = layers["technical"]
    normalized_asset_path = _normalize_path(asset_file_path)

    if normalized_asset_path and not technical.get("original_file_path"):
        technical["original_file_path"] = normalized_asset_path
    if asset_filename and not technical.get("original_file_name"):
        technical["original_file_name"] = asset_filename
    if asset_file_size is not None and not technical.get("original_file_size"):
        technical["original_file_size"] = asset_file_size
    if asset_mime_type and not technical.get("original_mime_type"):
        technical["original_mime_type"] = asset_mime_type

    has_distinct_original = bool(
        technical.get("original_file_path")
        and normalized_asset_path
        and technical.get("original_file_path") != normalized_asset_path
    )
    should_default_access_to_asset = bool(normalized_asset_path) and (
        has_distinct_original or not requires_iiif_access_derivative(layers)
    )
    if should_default_access_to_asset and normalized_asset_path:
        technical.setdefault("iiif_access_file_path", normalized_asset_path)
        technical.setdefault("iiif_access_file_name", os.path.basename(normalized_asset_path))
        if asset_mime_type:
            technical.setdefault("iiif_access_mime_type", asset_mime_type)

    return layers


def get_asset_original_file_path(asset: Asset) -> str | None:
    layers = populate_iiif_access_metadata(
        asset.metadata_info or {},
        asset_file_path=asset.file_path,
        asset_filename=asset.filename,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
    )
    technical = layers["technical"]
    return _normalize_path(technical.get("original_file_path")) or _normalize_path(asset.file_path)


def get_asset_iiif_access_file_path(
    asset: Asset,
    *,
    allow_original_fallback: bool = True,
    require_exists: bool = False,
) -> str | None:
    layers = populate_iiif_access_metadata(
        asset.metadata_info or {},
        asset_file_path=asset.file_path,
        asset_filename=asset.filename,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
    )
    technical = layers["technical"]
    iiif_access_path = _normalize_path(technical.get("iiif_access_file_path"))
    if iiif_access_path:
        if not require_exists or _path_exists(iiif_access_path):
            return iiif_access_path
        return None

    if allow_original_fallback and not requires_iiif_access_derivative(layers):
        original_path = get_asset_original_file_path(asset)
        if original_path and (not require_exists or _path_exists(original_path)):
            return original_path

    return None


def get_asset_primary_file_path(asset: Asset, *, require_exists: bool = False) -> str | None:
    iiif_access_path = get_asset_iiif_access_file_path(
        asset,
        allow_original_fallback=True,
        require_exists=require_exists,
    )
    if iiif_access_path:
        return iiif_access_path
    original_path = get_asset_original_file_path(asset)
    if original_path and (not require_exists or _path_exists(original_path)):
        return original_path
    return None


def get_asset_iiif_access_mime_type(asset: Asset) -> str | None:
    layers = populate_iiif_access_metadata(
        asset.metadata_info or {},
        asset_file_path=asset.file_path,
        asset_filename=asset.filename,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
    )
    technical = layers["technical"]
    iiif_mime_type = _normalize_path(technical.get("iiif_access_mime_type"))
    if iiif_mime_type:
        return iiif_mime_type

    iiif_access_path = get_asset_iiif_access_file_path(asset, allow_original_fallback=True, require_exists=False)
    if iiif_access_path == get_asset_original_file_path(asset):
        return asset.mime_type
    return IIIF_ACCESS_MIME_TYPE if iiif_access_path else asset.mime_type


def is_iiif_ready(asset: Asset) -> bool:
    if asset.status != "ready":
        return False
    return get_asset_iiif_access_file_path(asset, allow_original_fallback=True, require_exists=False) is not None


def build_iiif_access_output_path(asset: Asset) -> str:
    derivative_dir = os.path.join(config.UPLOAD_DIR, IIIF_ACCESS_DIR_NAME, f"asset-{asset.id}")
    return os.path.join(derivative_dir, IIIF_ACCESS_FILENAME)


def generate_pyramidal_tiff_access_copy(source_path: str, output_path: str) -> tuple[int, int]:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image = pyvips.Image.new_from_file(source_path, access="sequential")
    image.write_to_file(
        output_path,
        compression="deflate",
        tile=True,
        tile_width=IIIF_TILE_SIZE,
        tile_height=IIIF_TILE_SIZE,
        pyramid=True,
        bigtiff=True,
    )
    return int(image.width or 0), int(image.height or 0)


def mark_asset_ready_with_original_access(asset: Asset) -> None:
    layers = populate_iiif_access_metadata(
        asset.metadata_info or {},
        asset_file_path=asset.file_path,
        asset_filename=asset.filename,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
    )
    asset.metadata_info = layers
    asset.status = "ready"
    asset.process_message = "IIIF access is available from the preserved original."
    flag_modified(asset, "metadata_info")


def mark_asset_derivative_pending(asset: Asset) -> None:
    layers = populate_iiif_access_metadata(
        asset.metadata_info or {},
        asset_file_path=asset.file_path,
        asset_filename=asset.filename,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
    )
    asset.metadata_info = layers
    asset.status = "processing"
    asset.process_message = "IIIF access derivative is pending generation."
    flag_modified(asset, "metadata_info")


def apply_iiif_access_derivative(
    asset: Asset,
    *,
    output_path: str,
    width: int,
    height: int,
    conversion_method: str,
) -> None:
    layers = populate_iiif_access_metadata(
        asset.metadata_info or {},
        asset_file_path=asset.file_path,
        asset_filename=asset.filename,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
    )
    technical = layers["technical"]
    technical["iiif_access_file_path"] = output_path
    technical["iiif_access_file_name"] = os.path.basename(output_path)
    technical["iiif_access_mime_type"] = IIIF_ACCESS_MIME_TYPE
    technical["conversion_method"] = conversion_method
    if width > 0:
        technical["width"] = width
    if height > 0:
        technical["height"] = height

    asset.metadata_info = layers
    asset.status = "ready"
    asset.process_message = "IIIF access derivative is ready."
    flag_modified(asset, "metadata_info")
