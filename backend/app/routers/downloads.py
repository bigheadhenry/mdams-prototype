import hashlib
import os
import shutil
import tempfile
import zipfile
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Asset
from ..services.iiif_access import (
    get_asset_iiif_access_file_path,
    get_asset_original_file_path,
    get_asset_primary_file_path,
)
from ..services.metadata_layers import get_fixity_sha256

router = APIRouter(tags=["downloads"])


def _get_asset_or_404(asset_id: int, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


def _calculate_sha256(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as file_handle:
        for byte_block in iter(lambda: file_handle.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


@router.get("/assets/{asset_id}/download")
def download_asset_file(asset_id: int, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(asset_id, db)
    download_path = get_asset_primary_file_path(asset, require_exists=True)

    if not download_path:
        raise HTTPException(status_code=404, detail="Physical file not found")

    actual_filename = os.path.basename(download_path)
    return FileResponse(download_path, filename=actual_filename)


@router.get("/assets/{asset_id}/download-bag")
def download_asset_bag(asset_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(asset_id, db)

    original_file_path = get_asset_original_file_path(asset)
    if not original_file_path or not os.path.exists(original_file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")

    temp_dir = tempfile.mkdtemp()
    bag_name = f"bag_{asset_id}"
    bag_root = os.path.join(temp_dir, bag_name)
    data_dir = os.path.join(bag_root, "data")

    os.makedirs(data_dir, exist_ok=True)

    try:
        manifest_entries: list[str] = []
        fixity_sha256 = get_fixity_sha256(asset.metadata_info) or _calculate_sha256(original_file_path)

        original_basename = os.path.basename(original_file_path)
        dest_original_path = os.path.join(data_dir, original_basename)
        shutil.copy2(original_file_path, dest_original_path)
        manifest_entries.append(f"{fixity_sha256}  data/{original_basename}")

        iiif_access_path = get_asset_iiif_access_file_path(
            asset,
            allow_original_fallback=False,
            require_exists=True,
        )
        if iiif_access_path and iiif_access_path != original_file_path:
            iiif_access_basename = os.path.basename(iiif_access_path)
            dest_access_path = os.path.join(data_dir, iiif_access_basename)
            shutil.copy2(iiif_access_path, dest_access_path)
            manifest_entries.append(f"{_calculate_sha256(iiif_access_path)}  data/{iiif_access_basename}")

        with open(os.path.join(bag_root, "manifest-sha256.txt"), "w", encoding="utf-8") as file_handle:
            for entry in manifest_entries:
                file_handle.write(f"{entry}\n")

        with open(os.path.join(bag_root, "bagit.txt"), "w", encoding="utf-8") as file_handle:
            file_handle.write("BagIt-Version: 1.0\n")
            file_handle.write("Tag-File-Character-Encoding: UTF-8\n")

        with open(os.path.join(bag_root, "bag-info.txt"), "w", encoding="utf-8") as file_handle:
            file_handle.write("Source-Organization: MEAM Prototype\n")
            file_handle.write(f"Bagging-Date: {datetime.now().strftime('%Y-%m-%d')}\n")
            file_handle.write(f"Payload-Oxum: {asset.file_size}.1\n")
            file_handle.write(f"Original-File: {original_basename}\n")
            if iiif_access_path and iiif_access_path != original_file_path:
                file_handle.write(f"IIIF-Access-File: {os.path.basename(iiif_access_path)}\n")

        zip_filename = f"{bag_name}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _dirs, files in os.walk(bag_root):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)

        background_tasks.add_task(shutil.rmtree, temp_dir)

        return FileResponse(zip_path, media_type="application/zip", filename=zip_filename)

    except Exception as exc:
        shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Failed to generate bag: {str(exc)}")
