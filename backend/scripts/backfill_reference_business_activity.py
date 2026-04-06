from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://meam:meam_secret@localhost:5432/meam_db")


def _bootstrap_app(database_url: str) -> None:
    os.environ.setdefault("DATABASE_URL", database_url)


def _first_present(*values):
    for value in values:
        if value not in (None, "", []):
            return value
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill business activity profile fields from preserved reference raw metadata.")
    parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL, help="PostgreSQL database URL to use.")
    args = parser.parse_args()

    _bootstrap_app(args.database_url)
    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from app.database import SessionLocal
    from app.models import Asset
    from sqlalchemy.orm.attributes import flag_modified

    session = SessionLocal()
    updated = 0
    try:
        assets = session.query(Asset).filter(Asset.id.between(2, 13)).order_by(Asset.id).all()
        for asset in assets:
            metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
            profile = metadata.get("profile") if isinstance(metadata.get("profile"), dict) else {}
            if profile.get("key") != "business_activity":
                continue

            fields = profile.get("fields") if isinstance(profile.get("fields"), dict) else {}
            raw_metadata = metadata.get("raw_metadata") if isinstance(metadata.get("raw_metadata"), dict) else {}
            client_metadata = raw_metadata.get("client_metadata") if isinstance(raw_metadata.get("client_metadata"), dict) else {}
            raw_reference = client_metadata.get("raw_metadata") if isinstance(client_metadata.get("raw_metadata"), dict) else {}
            reference_modality = raw_reference.get("reference_modality") if isinstance(raw_reference.get("reference_modality"), dict) else {}
            reference_source_record = raw_reference.get("reference_source_record") if isinstance(raw_reference.get("reference_source_record"), dict) else {}
            reference_unified_json = raw_reference.get("reference_unified_json") if isinstance(raw_reference.get("reference_unified_json"), dict) else {}

            unified_layers = reference_unified_json.get("metadata_layers") if isinstance(reference_unified_json.get("metadata_layers"), dict) else {}
            unified_modality = unified_layers.get("modality") if isinstance(unified_layers.get("modality"), dict) else {}
            unified_source_record = unified_layers.get("source_record") if isinstance(unified_layers.get("source_record"), dict) else {}

            main_location = _first_present(
                fields.get("main_location"),
                reference_modality.get("主题地点"),
                reference_source_record.get("主题地点"),
                unified_modality.get("主题地点"),
                unified_source_record.get("主题地点"),
                reference_modality.get("主要地点"),
                reference_source_record.get("主要地点"),
            )
            main_person = _first_present(
                fields.get("main_person"),
                reference_modality.get("主要人物"),
                reference_source_record.get("主要人物"),
                unified_modality.get("主要人物"),
                unified_source_record.get("主要人物"),
            )

            changed = False
            if main_location not in (None, "", []) and fields.get("main_location") != main_location:
                fields["main_location"] = main_location
                changed = True
            if main_person not in (None, "", []) and fields.get("main_person") != main_person:
                fields["main_person"] = main_person
                changed = True

            if changed:
                profile["fields"] = fields
                metadata["profile"] = profile
                asset.metadata_info = json.loads(json.dumps(metadata, ensure_ascii=False))
                flag_modified(asset, "metadata_info")
                updated += 1
                print(f"[UPDATED] asset {asset.id} -> main_location={fields.get('main_location')!r}, main_person={fields.get('main_person')!r}")

        session.commit()
        print(f"Backfilled {updated} business activity assets")
    finally:
        session.close()


if __name__ == "__main__":
    main()
