import hashlib
import json
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..models import Asset
from ..schemas import IngestSipResponse
from ..services.iiif_access import (
    get_asset_iiif_access_file_path,
    mark_asset_derivative_pending,
    mark_asset_ready_with_original_access,
)
from ..services.metadata_layers import build_metadata_layers
from ..tasks import generate_iiif_access_derivative
from ..utils.metadata import extract_metadata

router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
    responses={404: {"description": "Not found"}},
)


@router.post("/sip", response_model=IngestSipResponse)
async def ingest_sip(
    file: UploadFile = File(...),
    manifest: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Receive SIP (Submission Information Package) with BagIt-like verification.
    鎺ユ敹 SIP 鍖呭苟杩涜 BagIt 椋庢牸鐨勬牎楠屻€?

    - **file**: The binary file stream (image).
    - **manifest**: JSON string containing metadata and client-side calculated SHA256 hash.
    """

    try:
        manifest_data = json.loads(manifest)
        client_hash = manifest_data.get("hash")
        client_metadata = manifest_data.get("metadata", {})

        if not client_hash:
            raise HTTPException(status_code=400, detail="Manifest missing SHA256 hash")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON manifest")

    sha256_hash = hashlib.sha256()
    file_location = os.path.join(config.UPLOAD_DIR, file.filename)
    temp_location = file_location + ".tmp"

    try:
        with open(temp_location, "wb") as buffer:
            while content := await file.read(64 * 1024):
                sha256_hash.update(content)
                buffer.write(content)

        server_hash = sha256_hash.hexdigest()
        if server_hash.lower() != client_hash.lower():
            os.remove(temp_location)
            raise HTTPException(
                status_code=400,
                detail=f"Fixity Check Failed! Client: {client_hash}, Server: {server_hash}"
            )

        if os.path.exists(file_location):
            os.remove(file_location)
        os.rename(temp_location, file_location)

        file_size = os.path.getsize(file_location)
        exif_metadata = extract_metadata(file_location)

        width, height = 0, 0
        try:
            with Image.open(file_location) as img:
                width, height = img.size
        except Exception:
            pass

        if width == 0 or height == 0:
            try:
                file_group = exif_metadata.get("File", {})
                width = file_group.get("ImageWidth", 0)
                height = file_group.get("ImageHeight", 0)

                if width == 0 or height == 0:
                    composite_group = exif_metadata.get("Composite", {})
                    image_size = composite_group.get("ImageSize")
                    if image_size and "x" in str(image_size):
                        image_width, image_height = str(image_size).split("x", 1)
                        width = int(image_width)
                        height = int(image_height)
            except Exception as exc:
                print(f"Error extracting dimensions with ExifTool: {exc}")

        file_group = exif_metadata.get("File", {})
        image_file_name = file.filename
        normalized_visibility_scope = str(client_metadata.get("visibility_scope") or "open").strip().lower()
        if normalized_visibility_scope not in {"open", "owner_only"}:
            normalized_visibility_scope = "open"
        collection_object_id = client_metadata.get("collection_object_id")
        if isinstance(collection_object_id, str) and collection_object_id.isdigit():
            collection_object_id = int(collection_object_id)
        if not isinstance(collection_object_id, int):
            collection_object_id = None

        final_metadata = build_metadata_layers(
            asset_filename=file.filename,
            asset_file_path=file_location,
            asset_file_size=file_size,
            asset_mime_type=file.content_type,
            asset_status="processing",
            asset_resource_type="image_2d_cultural_object",
            asset_visibility_scope=normalized_visibility_scope,
            asset_collection_object_id=collection_object_id,
            metadata={
                **client_metadata,
                "ingest_method": "sip_bagit",
                "fixity_sha256": server_hash,
                "checksum": server_hash,
                "checksum_algorithm": "SHA256",
                "original_file_name": file.filename,
                "image_file_name": image_file_name,
                "file_size": file_size,
                "format_name": file_group.get("FileType") or file.content_type,
                "format_version": file_group.get("FileTypeVersion"),
                "width": width,
                "height": height,
                "visibility_scope": normalized_visibility_scope,
                "collection_object_id": collection_object_id,
            },
            source_metadata={
                "client_metadata": client_metadata,
                "exif_metadata": exif_metadata,
                "server_hash": server_hash,
                "visibility_scope": normalized_visibility_scope,
                "collection_object_id": collection_object_id,
            },
        )

        db_asset = Asset(
            filename=file.filename,
            file_path=file_location,
            file_size=file_size,
            mime_type=file.content_type,
            visibility_scope=normalized_visibility_scope,
            collection_object_id=collection_object_id,
            status="processing",
            resource_type="image_2d_cultural_object",
            process_message="SIP received and awaiting IIIF access decision.",
            metadata_info=final_metadata
        )

        if get_asset_iiif_access_file_path(db_asset, allow_original_fallback=False):
            mark_asset_ready_with_original_access(db_asset)
        else:
            mark_asset_derivative_pending(db_asset)

        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)

        if db_asset.status == "processing":
            generate_iiif_access_derivative.delay(db_asset.id, file_location)

        return {
            "status": "success",
            "message": "SIP Ingested and Verified",
            "asset_id": db_asset.id,
            "fixity_check": "PASS",
            "sha256": server_hash
        }

    except Exception as e:
        if os.path.exists(temp_location):
            os.remove(temp_location)
        raise e
