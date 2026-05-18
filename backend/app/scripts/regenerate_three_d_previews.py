"""
Regenerate SVG turntable preview frames for all existing 3D assets.

Usage (inside backend container):
    python -m app.scripts.regenerate_three_d_previews

This will:
  1. Query all ThreeDAsset records
  2. Rebuild resource directory path
  3. Read file records from ThreeDAssetFile table
  4. Call build_three_d_preview_data to regenerate SVG frames
  5. Update metadata_info.raw_metadata.preview_data in the database
  6. Regenerate the preview JSON file on disk
"""

from __future__ import annotations

from pathlib import Path

import app.config
from app.database import SessionLocal
from app.models import ThreeDAsset, ThreeDAssetFile
from app.services.three_d_preview import build_three_d_preview_data


def _resource_dir(asset_id: int) -> Path:
    return Path(app.config.UPLOAD_DIR) / "three-d" / str(asset_id)


def _get_title(asset: ThreeDAsset) -> str:
    """Extract the display title from metadata_info layers."""
    info = asset.metadata_info or {}
    # Try core first, then technical, then raw_metadata, then fallback to filename
    core = info.get("core") or {}
    if isinstance(core, dict) and core.get("title"):
        return str(core["title"])
    raw = info.get("raw_metadata") or {}
    if isinstance(raw, dict):
        for key in ("title", "name", "model_name", "scene_name", "package_name"):
            if raw.get(key):
                return str(raw[key])
    technical = info.get("technical") or {}
    if isinstance(technical, dict) and technical.get("original_file_name"):
        return str(technical["original_file_name"])
    return asset.filename


def _file_records_from_db(asset: ThreeDAsset) -> list[dict]:
    """Build the file_records list expected by build_three_d_preview_data."""
    records: list[dict] = []
    for f in asset.files or []:
        records.append(
            {
                "role": f.role or "other",
                "role_label": f.role_label or f.role or "其他",
                "filename": f.filename,
                "actual_filename": f.actual_filename or f.filename,
                "file_path": str(f.file_path),
                "file_size": f.file_size or 0,
                "mime_type": f.mime_type or "application/octet-stream",
                "sort_order": f.sort_order or 0,
                "is_primary": bool(f.is_primary),
            }
        )
    return records


def _inject_preview_data(metadata_info: dict | None, preview_data: dict) -> dict:
    """Inject the new preview_data into metadata_info.raw_metadata."""
    if metadata_info is None:
        metadata_info = {}
    # Ensure raw_metadata exists
    raw = metadata_info.get("raw_metadata")
    if not isinstance(raw, dict):
        raw = {}
        metadata_info["raw_metadata"] = raw
    raw["preview_data"] = preview_data
    return metadata_info


def main() -> None:
    db = SessionLocal()
    try:
        assets = db.query(ThreeDAsset).order_by(ThreeDAsset.id).all()
        if not assets:
            print("No 3D assets found in database. Nothing to do.")
            return

        print(f"Found {len(assets)} 3D assets. Regenerating preview frames...")
        updated_count = 0
        for asset in assets:
            asset_id = asset.id
            resource_dir = _resource_dir(asset_id)
            if not resource_dir.exists():
                print(f"  [SKIP] Asset {asset_id}: resource directory not found at {resource_dir}")
                continue

            file_records = _file_records_from_db(asset)
            if not file_records:
                print(f"  [SKIP] Asset {asset_id}: no file records found in database")
                continue

            title = _get_title(asset)
            print(f"  Asset {asset_id}: '{title}' ({len(file_records)} files) ... ", end="", flush=True)

            preview_data = build_three_d_preview_data(
                resource_dir,
                asset_id=asset_id,
                title=title,
                file_records=file_records,
            )

            # Update database
            new_metadata = _inject_preview_data(asset.metadata_info, preview_data)
            asset.metadata_info = new_metadata

            updated_count += 1
            print(f"OK ({preview_data['frame_count']} frames)")

        db.commit()
        print(f"\nDone. Updated {updated_count} / {len(assets)} assets.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
