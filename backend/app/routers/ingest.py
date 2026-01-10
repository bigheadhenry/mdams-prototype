from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Asset
import os
import hashlib
import json
import shutil
from datetime import datetime
from PIL import Image

router = APIRouter(
    prefix="/ingest",
    tags=["ingest"],
    responses={404: {"description": "Not found"}},
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

@router.post("/sip")
async def ingest_sip(
    file: UploadFile = File(...),
    manifest: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Receive SIP (Submission Information Package) with BagIt-like verification.
    接收 SIP 包并进行 BagIt 风格的校验。
    
    - **file**: The binary file stream (image).
    - **manifest**: JSON string containing metadata and client-side calculated SHA256 hash.
    """
    
    # 1. Parse Manifest
    try:
        manifest_data = json.loads(manifest)
        client_hash = manifest_data.get("hash")
        client_metadata = manifest_data.get("metadata", {})
        
        if not client_hash:
            raise HTTPException(status_code=400, detail="Manifest missing SHA256 hash")
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON manifest")

    # 2. Receive File & Calculate Server-side Hash (Streamed)
    # 边接收边计算 Hash，避免多次读取 IO
    sha256_hash = hashlib.sha256()
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    
    # Use a temporary file first to ensure integrity before "committing" to storage
    temp_location = file_location + ".tmp"
    
    try:
        with open(temp_location, "wb") as buffer:
            # 64KB chunks
            while content := await file.read(64 * 1024):
                sha256_hash.update(content)
                buffer.write(content)
                
        server_hash = sha256_hash.hexdigest()
        
        # 3. Fixity Check (BagIt Verification)
        # 完整性校验
        if server_hash.lower() != client_hash.lower():
            os.remove(temp_location)
            raise HTTPException(
                status_code=400, 
                detail=f"Fixity Check Failed! Client: {client_hash}, Server: {server_hash}"
            )
            
        # 4. Finalize Storage
        # 校验通过，重命名为正式文件
        if os.path.exists(file_location):
             # Overwrite strategy for prototype
             os.remove(file_location)
        os.rename(temp_location, file_location)
        
        # 5. Save to Database
        file_size = os.path.getsize(file_location)
        
        # Extract dimensions
        width, height = 0, 0
        try:
            with Image.open(file_location) as img:
                width, height = img.size
        except Exception as e:
            print(f"Error extracting dimensions: {e}")

        # Merge technical metadata
        final_metadata = {
            "ingest_method": "sip_bagit",
            "fixity_sha256": server_hash,
            "original_metadata": client_metadata,
            "width": width,
            "height": height
        }
        
        db_asset = Asset(
            filename=file.filename,
            file_path=file_location,
            file_size=file_size,
            mime_type=file.content_type,
            status="ready",
            metadata_info=final_metadata
        )
        
        db.add(db_asset)
        db.commit()
        db.refresh(db_asset)
        
        return {
            "status": "success",
            "message": "SIP Ingested and Verified",
            "asset_id": db_asset.id,
            "fixity_check": "PASS",
            "sha256": server_hash
        }
        
    except Exception as e:
        # Cleanup temp file on error
        if os.path.exists(temp_location):
            os.remove(temp_location)
        raise e
