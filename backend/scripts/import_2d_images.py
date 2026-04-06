from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from PIL import Image

DEFAULT_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://meam:meam_secret@localhost:5432/meam_db")


def _bootstrap_app(database_url: str, upload_dir: str) -> None:
    os.environ.setdefault("DATABASE_URL", database_url)
    os.environ.setdefault("UPLOAD_DIR", upload_dir)


def _iter_jpeg_files(source_dir: Path) -> Iterable[Path]:
    for path in sorted(source_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg"}:
            yield path


def _select_sample(files: list[Path], limit: int) -> list[Path]:
    if limit <= 0 or limit >= len(files):
        return files
    if limit == 1:
        return [files[0]]
    selected: list[Path] = []
    last_index = len(files) - 1
    for index in range(limit):
        position = round(index * last_index / (limit - 1))
        candidate = files[position]
        if candidate not in selected:
            selected.append(candidate)
    if len(selected) < limit:
        for candidate in files:
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) >= limit:
                break
    return selected[:limit]


def _derive_object_number(filename: str) -> str | None:
    stem = Path(filename).stem
    if "__" in stem:
        stem = stem.split("__", 1)[0]
    return stem or None


def _build_metadata(source_file: Path, copied_file: Path, project_name: str) -> dict[str, object]:
    object_number = _derive_object_number(source_file.name)
    object_name = object_number
    checksum = hashlib.sha256(copied_file.read_bytes()).hexdigest()

    width = 0
    height = 0
    try:
        with Image.open(copied_file) as image:
            width, height = image.size
    except Exception:
        pass

    return {
        "title": object_name or source_file.stem,
        "image_category": "鐢熸椿鐢ㄥ叿",
        "project_type": "DigicolPhotoScan",
        "project_name": project_name,
        "image_name": source_file.stem,
        "capture_content": "鐢熸椿鐢ㄥ叿鍥剧墖閲囬泦鏍锋湰",
        "remark": "Imported from reference dataset",
        "tags": "鐢熸椿鐢ㄥ叿,DigicolPhotoScan",
        "record_account": "codex",
        "record_time": datetime.now(timezone.utc).isoformat(),
        "image_record_time": datetime.now(timezone.utc).isoformat(),
        "object_number": object_number,
        "object_name": object_name,
        "fixity_sha256": checksum,
        "checksum": checksum,
        "checksum_algorithm": "SHA256",
        "original_file_name": source_file.name,
        "image_file_name": source_file.name,
        "file_size": copied_file.stat().st_size,
        "format_name": "JPEG",
        "width": width,
        "height": height,
        "ingest_method": "reference_import",
        "original_file_path": str(source_file),
        "original_mime_type": "image/jpeg",
        "source_file": source_file.name,
        "source_folder": str(source_file.parent),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import 2D reference images into MDAMS.")
    parser.add_argument("--source", required=True, help="Source folder containing JPG/JPEG images.")
    parser.add_argument("--limit", type=int, default=12, help="Maximum number of files to import.")
    parser.add_argument("--project-name", default="鐢熸椿鐢ㄥ叿", help="Project name to write into management metadata.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL, help="PostgreSQL database URL to use.")
    parser.add_argument("--upload-dir", default="uploads", help="Upload directory to copy files into.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be imported without copying files.")
    args = parser.parse_args()

    source_dir = Path(args.source).expanduser().resolve()
    upload_dir = Path(args.upload_dir).expanduser().resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)

    if not source_dir.exists():
        raise SystemExit(f"Source directory not found: {source_dir}")

    _bootstrap_app(args.database_url, str(upload_dir))

    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from app.database import Base, SessionLocal, engine
    from app.models import Asset
    from app.services.metadata_layers import build_metadata_layers

    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        existing_filenames = {row[0] for row in session.query(Asset.filename).all()}
        imported = 0
        skipped = 0

        source_files = list(_iter_jpeg_files(source_dir))
        for source_file in _select_sample(source_files, args.limit):
            if imported >= args.limit:
                break
            if source_file.name in existing_filenames:
                skipped += 1
                continue

            target_file = upload_dir / source_file.name
            if not args.dry_run:
                shutil.copy2(source_file, target_file)

            metadata = _build_metadata(source_file, target_file if target_file.exists() else source_file, args.project_name)
            metadata_layers = build_metadata_layers(
                asset_filename=source_file.name,
                asset_file_path=str(target_file),
                asset_file_size=target_file.stat().st_size if target_file.exists() else source_file.stat().st_size,
                asset_mime_type="image/jpeg",
                asset_status="ready",
                asset_resource_type="image_2d_cultural_object",
                metadata=metadata,
                source_metadata={
                    "source_file": source_file.name,
                    "source_folder": str(source_file.parent),
                    "source_system": "digicol_photoscan",
                    "source_category": "鐢熸椿鐢ㄥ叿",
                },
                profile_hint="movable_artifact",
            )

            if args.dry_run:
                print(f"[DRY-RUN] {source_file.name}")
                imported += 1
                continue

            asset = Asset(
                filename=source_file.name,
                file_path=str(target_file),
                file_size=target_file.stat().st_size,
                mime_type="image/jpeg",
                status="ready",
                resource_type="image_2d_cultural_object",
                process_message="Imported from DigicolPhotoScan living utensils dataset",
                metadata_info=metadata_layers,
            )
            session.add(asset)
            session.flush()
            imported += 1

        if not args.dry_run:
            session.commit()

        print(f"Imported {imported} files from {source_dir}")
        if skipped:
            print(f"Skipped {skipped} existing files")
    finally:
        session.close()


if __name__ == "__main__":
    main()

