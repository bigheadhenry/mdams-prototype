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
from ..services.metadata_layers import get_fixity_sha256, get_original_file_path

router = APIRouter(tags=["downloads"])


def _get_asset_or_404(asset_id: int, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/assets/{asset_id}/download")
def download_asset_file(asset_id: int, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(asset_id, db)

    if not asset.file_path or not os.path.exists(asset.file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")

    actual_filename = os.path.basename(asset.file_path)
    return FileResponse(asset.file_path, filename=actual_filename)


@router.get("/assets/{asset_id}/download-bag")
def download_asset_bag(asset_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(asset_id, db)

    if not os.path.exists(asset.file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")

    temp_dir = tempfile.mkdtemp()
    bag_name = f"bag_{asset_id}"
    bag_root = os.path.join(temp_dir, bag_name)
    data_dir = os.path.join(bag_root, "data")

    os.makedirs(data_dir, exist_ok=True)

    try:
        actual_filename = os.path.basename(asset.file_path)
        dest_path = os.path.join(data_dir, actual_filename)
        shutil.copy2(asset.file_path, dest_path)

        original_file_path = get_original_file_path(asset.metadata_info)
        fixity_sha256 = get_fixity_sha256(asset.metadata_info) or "unknown"

        manifest_entries = []
        manifest_entries.append(f"{fixity_sha256}  data/{actual_filename}")

        if original_file_path and os.path.exists(original_file_path) and original_file_path != asset.file_path:
            original_basename = os.path.basename(original_file_path)
            dest_original_path = os.path.join(data_dir, original_basename)
            shutil.copy2(original_file_path, dest_original_path)
            manifest_entries.append(f"{fixity_sha256}  data/{original_basename}")

            def calculate_sha256(filepath):
                sha256_hash = hashlib.sha256()
                with open(filepath, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                return sha256_hash.hexdigest()

            converted_hash = calculate_sha256(asset.file_path)
            manifest_entries[0] = f"{converted_hash}  data/{actual_filename}"

        with open(os.path.join(bag_root, "manifest-sha256.txt"), "w", encoding="utf-8") as f:
            for entry in manifest_entries:
                f.write(f"{entry}\n")

        with open(os.path.join(bag_root, "bagit.txt"), "w", encoding="utf-8") as f:
            f.write("BagIt-Version: 1.0\n")
            f.write("Tag-File-Character-Encoding: UTF-8\n")

        with open(os.path.join(bag_root, "bag-info.txt"), "w", encoding="utf-8") as f:
            f.write("Source-Organization: MEAM Prototype\n")
            f.write(f"Bagging-Date: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"Payload-Oxum: {asset.file_size}.1\n")
            if original_file_path:
                f.write(f"Original-File: {os.path.basename(original_file_path)}\n")

        zip_filename = f"{bag_name}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(bag_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)

        background_tasks.add_task(shutil.rmtree, temp_dir)

        return FileResponse(zip_path, media_type="application/zip", filename=zip_filename)

    except Exception as e:
        shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Failed to generate bag: {str(e)}")
