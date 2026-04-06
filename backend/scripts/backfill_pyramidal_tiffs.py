from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pyvips


PYRAMIDAL_TIFF_EXTENSIONS = {".tif", ".tiff", ".psb"}
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://meam:meam_secret@localhost:5432/meam_db")
DEFAULT_UPLOAD_DIR = str(REPO_ROOT / "uploads")


def _bootstrap_app(database_url: str, upload_dir: str) -> None:
    os.environ.setdefault("DATABASE_URL", database_url)
    os.environ.setdefault("UPLOAD_DIR", upload_dir)


def _coerce_int(value: object) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0


def _is_large_tiff_candidate(asset) -> bool:
    filename = str(getattr(asset, "filename", "") or "")
    file_path = str(getattr(asset, "file_path", "") or "")
    mime_type = str(getattr(asset, "mime_type", "") or "").lower()
    suffix = Path(filename or file_path).suffix.lower()
    if suffix not in PYRAMIDAL_TIFF_EXTENSIONS and mime_type not in {"image/tiff", "image/x-tiff", "image/tif"}:
        return False

    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    technical = metadata.get("technical") if isinstance(metadata, dict) else {}
    if isinstance(technical, dict):
        conversion_method = str(technical.get("conversion_method") or "").lower()
        if "pyramidal" in conversion_method or technical.get("iiif_access_file_path"):
            return False
        if technical.get("iiif_access_file_path") and os.path.exists(str(technical.get("iiif_access_file_path"))):
            return False

    return True


def _build_derivative_path(upload_dir: Path, asset_id: int, source_path: Path) -> Path:
    derivative_dir = upload_dir / "derivatives" / f"asset-{asset_id}"
    derivative_dir.mkdir(parents=True, exist_ok=True)
    stem = source_path.stem
    return derivative_dir / f"{stem}.pyramidal.tiff"


def _convert_to_pyramidal_tiff(source_path: Path, target_path: Path) -> tuple[int, int]:
    image = pyvips.Image.new_from_file(str(source_path), access="sequential")
    width = max(int(image.width or 0), 0)
    height = max(int(image.height or 0), 0)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    image.write_to_file(
        str(target_path),
        compression="deflate",
        tile=True,
        tile_width=256,
        tile_height=256,
        pyramid=True,
        bigtiff=True,
        strip=True,
    )
    return width, height


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill pyramidal tiled TIFF derivatives for existing 2D assets.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL, help="PostgreSQL database URL to use.")
    parser.add_argument("--upload-dir", default=DEFAULT_UPLOAD_DIR, help="Upload directory containing stored assets.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be converted without writing files.")
    parser.add_argument("--force", action="store_true", help="Recreate derivatives even when an existing access copy is recorded.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of assets processed. 0 means no limit.")
    args = parser.parse_args()

    upload_dir = Path(args.upload_dir).expanduser()
    if not upload_dir.is_absolute():
        upload_dir = (REPO_ROOT / upload_dir).resolve()
    else:
        upload_dir = upload_dir.resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    _bootstrap_app(args.database_url, str(upload_dir))

    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from app.database import SessionLocal
    from app.models import Asset
    from app.services.derivative_policy import infer_derivative_policy_from_metadata
    from app.services.metadata_layers import build_metadata_layers
    from sqlalchemy.orm.attributes import flag_modified

    session = SessionLocal()
    converted = 0
    skipped = 0
    failed = 0
    try:
        assets = session.query(Asset).order_by(Asset.id.asc()).all()
        for asset in assets:
            if args.limit and converted >= args.limit:
                break
            if not _is_large_tiff_candidate(asset):
                skipped += 1
                continue

            source_path = Path(asset.file_path)
            if not source_path.exists():
                print(f"[SKIP] asset {asset.id}: source file missing -> {source_path}")
                skipped += 1
                continue

            metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
            policy = infer_derivative_policy_from_metadata(metadata)
            if policy.get("derivative_strategy") != "generate_pyramidal_tiff":
                skipped += 1
                continue

            technical = metadata.get("technical") if isinstance(metadata.get("technical"), dict) else {}
            existing_access_path = str(technical.get("iiif_access_file_path") or "")
            if existing_access_path and os.path.exists(existing_access_path) and not args.force:
                skipped += 1
                continue

            target_path = _build_derivative_path(upload_dir, asset.id, source_path)
            if target_path.exists() and not args.force:
                print(f"[SKIP] asset {asset.id}: derivative already exists -> {target_path}")
                skipped += 1
                continue

            print(f"[CONVERT] asset {asset.id}: {source_path.name} -> {target_path}")
            if not args.dry_run:
                try:
                    width, height = _convert_to_pyramidal_tiff(source_path, target_path)
                except Exception as exc:
                    failed += 1
                    print(f"[FAIL] asset {asset.id}: {exc}")
                    continue

                original_file_size = _coerce_int(asset.file_size)
                original_mime_type = str(asset.mime_type or "").strip() or "image/tiff"
                asset.file_path = str(target_path)
                asset.file_size = target_path.stat().st_size
                asset.mime_type = "image/tiff"
                asset.status = "ready"
                asset.process_message = "Pyramidal tiled TIFF backfill completed"

                merged_metadata = json.loads(json.dumps(metadata, ensure_ascii=False))
                technical = merged_metadata.get("technical") if isinstance(merged_metadata.get("technical"), dict) else {}
                technical["original_file_path"] = str(source_path)
                technical["original_file_name"] = source_path.name
                technical["original_file_size"] = original_file_size
                technical["original_mime_type"] = original_mime_type
                technical["iiif_access_file_path"] = str(target_path)
                technical["iiif_access_file_name"] = target_path.name
                technical["iiif_access_mime_type"] = "image/tiff"
                technical["conversion_method"] = "backfill_pyvips_pyramidal_tiff"
                technical["width"] = width
                technical["height"] = height
                merged_metadata["technical"] = technical

                rebuilt = build_metadata_layers(
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
                    metadata=merged_metadata,
                )
                asset.metadata_info = rebuilt
                flag_modified(asset, "metadata_info")
                session.commit()
                converted += 1
                print(f"[DONE] asset {asset.id}: {asset.file_size} bytes, {width}x{height}")
            else:
                converted += 1

        print(f"Converted {converted} assets, skipped {skipped}, failed {failed}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
