from __future__ import annotations

import os

import pyvips
from PIL import Image, ImageOps

from .. import config
from ..models import Asset
from .metadata_layers import get_iiif_access_file_path, get_original_file_path

PREVIEW_DIR_NAME = "previews"
PREVIEW_FILE_SUFFIX = ".preview.jpg"
PREVIEW_MAX_WIDTH = 1600
PREVIEW_JPEG_QUALITY = 82


def get_preview_image_path(asset: Asset) -> str:
    base_dir = os.path.join(config.UPLOAD_DIR, PREVIEW_DIR_NAME)
    return os.path.join(base_dir, f"asset-{asset.id}{PREVIEW_FILE_SUFFIX}")


def _get_preview_source_path(asset: Asset) -> str | None:
    iiif_access_file_path = get_iiif_access_file_path(asset.metadata_info)
    if iiif_access_file_path and os.path.exists(iiif_access_file_path):
        return iiif_access_file_path

    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    technical = metadata.get("technical") if isinstance(metadata, dict) else {}
    if isinstance(technical, dict):
        preview_file_path = technical.get("preview_file_path")
        if isinstance(preview_file_path, str) and preview_file_path and os.path.exists(preview_file_path):
            return preview_file_path

    original_file_path = get_original_file_path(asset.metadata_info)
    if original_file_path and os.path.exists(original_file_path):
        return original_file_path

    if asset.file_path and os.path.exists(asset.file_path):
        return asset.file_path

    return None


def _generate_preview_with_pyvips(source_path: str, preview_path: str) -> None:
    image = pyvips.Image.new_from_file(source_path, access="sequential")
    width = max(int(image.width or 0), 1)
    scale = min(1.0, PREVIEW_MAX_WIDTH / width)
    if scale < 1.0:
        image = image.resize(scale)

    if image.bands == 4:
        image = image.flatten(background=[255, 255, 255])

    image.jpegsave(
        preview_path,
        Q=PREVIEW_JPEG_QUALITY,
        strip=True,
        optimize_coding=True,
        interlace=True,
    )


def _generate_preview_with_pillow(source_path: str, preview_path: str) -> None:
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
            converted = image.convert("RGBA")
            background = Image.new("RGB", converted.size, (255, 255, 255))
            background.paste(converted, mask=converted.getchannel("A"))
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")
        image.thumbnail((PREVIEW_MAX_WIDTH, PREVIEW_MAX_WIDTH), Image.Resampling.LANCZOS)
        image.save(preview_path, format="JPEG", quality=PREVIEW_JPEG_QUALITY, optimize=True, progressive=True)


def ensure_preview_image(asset: Asset) -> str | None:
    source_path = _get_preview_source_path(asset)
    if not source_path:
        return None

    preview_path = get_preview_image_path(asset)
    if os.path.exists(preview_path):
        return preview_path

    os.makedirs(os.path.dirname(preview_path), exist_ok=True)

    try:
        _generate_preview_with_pyvips(source_path, preview_path)
    except Exception:
        try:
            _generate_preview_with_pillow(source_path, preview_path)
        except Exception:
            return None

    return preview_path if os.path.exists(preview_path) else None
