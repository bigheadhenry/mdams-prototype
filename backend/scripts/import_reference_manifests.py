from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

DEFAULT_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://meam:meam_secret@localhost:5432/meam_db")

def _bootstrap_app(database_url: str, upload_dir: str) -> None:
    os.environ.setdefault("DATABASE_URL", database_url)
    os.environ.setdefault("UPLOAD_DIR", upload_dir)


async def _ingest_one(ingest_router, session, image_path: Path, import_filename: str, manifest: dict[str, object]) -> dict[str, object]:
    from fastapi import UploadFile
    from starlette.datastructures import Headers

    with image_path.open("rb") as handle:
        upload = UploadFile(
            file=handle,
            filename=import_filename,
            headers=Headers({"content-type": "image/tiff" if image_path.suffix.lower() in {".tif", ".tiff"} else "image/jpeg"}),
        )
        return await ingest_router.ingest_sip(
            file=upload,
            manifest=json.dumps(manifest, ensure_ascii=False),
            db=session,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Import reference resource package into the MDAMS 2D SIP ingest pipeline.")
    parser.add_argument("--source-root", required=True, help="Root folder of the reference resource package.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL, help="PostgreSQL database URL to use.")
    parser.add_argument("--upload-dir", default="uploads", help="Upload directory used by the ingest pipeline.")
    parser.add_argument("--visibility-scope", default="open", choices=["open", "owner_only"], help="Visibility scope to embed into imported assets.")
    parser.add_argument("--limit", type=int, default=0, help="Optional limit on imported candidate count.")
    parser.add_argument("--dry-run", action="store_true", help="List candidates without importing them.")
    args = parser.parse_args()

    source_root = Path(args.source_root).expanduser().resolve()
    upload_dir = Path(args.upload_dir).expanduser().resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)

    _bootstrap_app(args.database_url, str(upload_dir))

    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from app.database import Base, SessionLocal, engine
    from app.models import Asset
    from app.routers import ingest as ingest_router
    from app.services.reference_import import build_import_filename, collect_reference_candidates

    Base.metadata.create_all(bind=engine)

    candidates = collect_reference_candidates(
        source_root,
        visibility_scope=args.visibility_scope,
        limit=args.limit or None,
    )

    session = SessionLocal()
    imported = 0
    skipped = 0
    try:
        existing_filenames = {row[0] for row in session.query(Asset.filename).all()}
        for candidate in candidates:
            relative_dir = candidate.source_dir.relative_to(source_root)
            import_filename = build_import_filename(candidate.primary_image, relative_dir)
            if import_filename in existing_filenames:
                skipped += 1
                print(f"[SKIP] {relative_dir} -> {import_filename}")
                continue

            manifest = json.loads(json.dumps(candidate.manifest))
            metadata = manifest.get("metadata") or {}
            technical = metadata.get("technical") if isinstance(metadata.get("technical"), dict) else {}
            technical["original_file_name"] = candidate.primary_image.name
            technical["image_file_name"] = import_filename

            if args.dry_run:
                print(f"[DRY-RUN] {relative_dir} -> {import_filename}")
                imported += 1
                continue

            response = asyncio.run(
                _ingest_one(
                    ingest_router=ingest_router,
                    session=session,
                    image_path=candidate.primary_image,
                    import_filename=import_filename,
                    manifest=manifest,
                )
            )
            existing_filenames.add(import_filename)
            imported += 1
            print(f"[IMPORTED] {relative_dir} -> asset {response['asset_id']} ({import_filename})")

        print(f"Imported {imported} reference resources")
        if skipped:
            print(f"Skipped {skipped} already-imported resources")
    finally:
        session.close()


if __name__ == "__main__":
    main()
