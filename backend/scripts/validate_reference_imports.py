from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from starlette.requests import Request

DEFAULT_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://meam:meam_secret@localhost:5432/meam_db")


def _bootstrap_app(database_url: str, upload_dir: str) -> None:
    os.environ.setdefault("DATABASE_URL", database_url)
    os.environ.setdefault("UPLOAD_DIR", upload_dir)


def _build_request() -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/iiif/0/manifest",
        "raw_path": b"/api/iiif/0/manifest",
        "query_string": b"",
        "headers": [(b"host", b"localhost:8000")],
        "client": ("127.0.0.1", 8000),
        "server": ("localhost", 8000),
    }
    return Request(scope)


def _write_markdown(output_path: Path, rows: list[dict[str, object]]) -> None:
    lines = [
        "# Post-Import Validation Checklist",
        "",
        f"- Total assets: {len(rows)}",
        "",
        "| Asset ID | Title | Profile | Manifest | Download | BagIt | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        notes = "; ".join(row.get("notes", [])) if row.get("notes") else ""
        lines.append(
            f"| {row['asset_id']} | {row['title']} | {row['profile_key']} | {row['manifest_status']} | {row['download_status']} | {row['bag_status']} | {notes} |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate imported reference assets in the current 2D subsystem.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL, help="PostgreSQL database URL to use.")
    parser.add_argument("--upload-dir", default="uploads", help="Upload directory used by the ingest pipeline.")
    parser.add_argument("--output-dir", required=True, help="Directory to write the validation checklist into.")
    parser.add_argument("--asset-id-from", type=int, default=2, help="Inclusive lower asset id bound.")
    parser.add_argument("--asset-id-to", type=int, default=13, help="Inclusive upper asset id bound.")
    args = parser.parse_args()

    _bootstrap_app(args.database_url, str(Path(args.upload_dir).expanduser().resolve()))
    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from app.database import SessionLocal
    from app.permissions import build_system_user
    from app.routers import iiif as iiif_router
    from app.services.asset_detail import build_asset_detail_response
    from app.models import Asset

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    request = _build_request()
    user = build_system_user()
    session = SessionLocal()
    rows: list[dict[str, object]] = []
    try:
        for asset_id in range(args.asset_id_from, args.asset_id_to + 1):
            notes: list[str] = []
            manifest_status = "ok"
            download_status = "ok"
            bag_status = "ok"
            title = ""
            profile_key = ""

            try:
                manifest = iiif_router.get_iiif_manifest(asset_id=asset_id, request=request, db=session, user=user)
                title = str(manifest.get("label", {}).get("zh-cn", [manifest.get("label", {}).get("en", [""])])[0])
                items = manifest.get("items") or []
                if not items:
                    manifest_status = "fail"
                    notes.append("manifest has no items")
            except Exception as exc:
                manifest_status = "fail"
                notes.append(f"manifest error: {exc}")

            asset = session.get(Asset, asset_id)
            if asset is not None and isinstance(asset.metadata_info, dict):
                if not asset.file_path or not Path(asset.file_path).exists():
                    download_status = "fail"
                    notes.append("physical file missing on disk")

                detail = build_asset_detail_response(asset)
                if not detail.outputs.download_url:
                    download_status = "fail"
                    notes.append("missing download_url")
                if not detail.outputs.download_bag_url:
                    bag_status = "fail"
                    notes.append("missing download_bag_url")

                core = asset.metadata_info.get("core") if isinstance(asset.metadata_info.get("core"), dict) else {}
                profile = asset.metadata_info.get("profile") if isinstance(asset.metadata_info.get("profile"), dict) else {}
                title = str(core.get("title") or title or asset.filename)
                profile_key = str(profile.get("key") or "")
                fields = profile.get("fields") if isinstance(profile.get("fields"), dict) else {}
                if profile_key == "business_activity" and not fields.get("main_location"):
                    notes.append("business activity missing main_location")
            else:
                download_status = "fail"
                bag_status = "fail"
                notes.append("asset record not found")

            rows.append(
                {
                    "asset_id": asset_id,
                    "title": title,
                    "profile_key": profile_key,
                    "manifest_status": manifest_status,
                    "download_status": download_status,
                    "bag_status": bag_status,
                    "notes": notes,
                }
            )
    finally:
        session.close()

    json_path = output_dir / "post-import-validation.json"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path = output_dir / "post-import-validation.md"
    _write_markdown(md_path, rows)

    print(f"Validation JSON: {json_path}")
    print(f"Validation Markdown: {md_path}")


if __name__ == "__main__":
    main()
