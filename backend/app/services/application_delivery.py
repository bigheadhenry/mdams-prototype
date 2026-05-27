import json
import os
import shutil
import tempfile
import zipfile

from fastapi import HTTPException

from ..models import Application


def build_application_export_package(application: Application) -> tuple[str, str, str]:
    temp_dir = tempfile.mkdtemp()
    package_root = os.path.join(temp_dir, f"{application.application_no}")
    data_dir = os.path.join(package_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    manifest_items = []
    for item in application.items:
        asset = item.asset
        if asset is None:
            manifest_items.append(
                {
                    "application_item_id": item.id,
                    "asset_id": None,
                    "source_system": item.source_system,
                    "source_id": item.source_id,
                    "resource_type": item.resource_type,
                    "resource_title": item.resource_title,
                    "manifest_url": item.manifest_url,
                    "source_label": item.source_label,
                    "object_number": item.object_number,
                    "requested_variant": item.requested_variant,
                    "delivery_format": item.delivery_format,
                    "note": item.note,
                    "delivery_note": "This unified resource is recorded for review; no local 2D asset file was attached to this export package.",
                }
            )
            continue

        if not asset.file_path or not os.path.exists(asset.file_path):
            raise HTTPException(status_code=404, detail=f"Physical file missing for asset {asset.id}")

        actual_filename = os.path.basename(asset.file_path)
        safe_name = f"{asset.id}_{actual_filename}"
        export_path = os.path.join(data_dir, safe_name)
        shutil.copy2(asset.file_path, export_path)
        manifest_items.append(
            {
                "application_item_id": item.id,
                "asset_id": asset.id,
                "source_system": item.source_system or "image_2d",
                "source_id": item.source_id or str(asset.id),
                "resource_type": item.resource_type or asset.resource_type,
                "resource_title": item.resource_title or asset.filename,
                "manifest_url": item.manifest_url,
                "source_label": item.source_label,
                "object_number": item.object_number,
                "filename": asset.filename,
                "actual_filename": actual_filename,
                "export_filename": safe_name,
                "requested_variant": item.requested_variant,
                "delivery_format": item.delivery_format,
                "note": item.note,
            }
        )

    with open(os.path.join(package_root, "application.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "application_no": application.application_no,
                "requester_name": application.requester_name,
                "requester_org": application.requester_org,
                "contact_email": application.contact_email,
                "purpose": application.purpose,
                "usage_scope": application.usage_scope,
                "status": application.status,
                "review_note": application.review_note,
                "items": manifest_items,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    with open(os.path.join(package_root, "README.txt"), "w", encoding="utf-8") as f:
        f.write(f"Application No: {application.application_no}\n")
        f.write("This package contains the assets approved for delivery.\n")

    zip_path = os.path.join(temp_dir, f"{application.application_no}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(package_root):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)

    return temp_dir, zip_path, f"{application.application_no}.zip"
