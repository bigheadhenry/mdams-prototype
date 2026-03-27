import os

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..models import Asset
from ..schemas import AssetDetailResponse, AssetOut
from ..services.asset_detail import build_asset_detail_response
from ..services.metadata_layers import build_metadata_layers, get_original_file_path

router = APIRouter(tags=["assets"])


@router.get("/")
def read_root():
    return {"message": "Welcome to MEAM Prototype API"}


@router.post("/upload", response_model=AssetOut)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_location = os.path.join(config.UPLOAD_DIR, file.filename)
    os.makedirs(os.path.dirname(file_location), exist_ok=True)

    chunk_size = 64 * 1024
    with open(file_location, "wb") as buffer:
        while content := await file.read(chunk_size):
            buffer.write(content)

    file_size = os.path.getsize(file_location)
    width, height = 0, 0
    try:
        with Image.open(file_location) as img:
            width, height = img.size
    except Exception:
        pass

    db_asset = Asset(
        filename=file.filename,
        file_path=file_location,
        file_size=file_size,
        mime_type=file.content_type,
        status="ready",
        resource_type="image_2d_cultural_object",
        process_message="文件已上传并完成基础登记。",
        metadata_info=build_metadata_layers(
            asset_filename=file.filename,
            asset_file_path=file_location,
            asset_file_size=file_size,
            asset_mime_type=file.content_type,
            asset_status="ready",
            asset_resource_type="image_2d_cultural_object",
            metadata={
                "width": width,
                "height": height,
                "ingest_method": "upload",
                "original_file_name": file.filename,
                "image_file_name": os.path.basename(file_location),
                "file_size": file_size,
                "format_name": file.content_type,
            },
            source_metadata={
                "ingest_method": "upload",
                "file_name": file.filename,
                "file_size": file_size,
            },
        ),
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)

    return db_asset


@router.get("/debug/files")
def list_uploaded_files():
    try:
        files = []
        for filename in os.listdir(config.UPLOAD_DIR):
            filepath = os.path.join(config.UPLOAD_DIR, filename)
            stat = os.stat(filepath)
            files.append(
                {
                    "filename": filename,
                    "size": stat.st_size,
                    "permissions": oct(stat.st_mode)[-3:],
                    "uid": stat.st_uid,
                    "gid": stat.st_gid,
                }
            )
        return {
            "upload_dir": config.UPLOAD_DIR,
            "abs_path": os.path.abspath(config.UPLOAD_DIR),
            "files": files,
            "dir_permissions": oct(os.stat(config.UPLOAD_DIR).st_mode)[-3:],
        }
    except Exception as e:
        return {"error": str(e)}


def _get_asset_or_404(asset_id: int, db: Session) -> Asset:
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.get("/assets", response_model=list[AssetOut])
def list_assets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Asset).offset(skip).limit(limit).all()


@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(asset_id, db)

    try:
        if os.path.exists(asset.file_path):
            os.remove(asset.file_path)
        if asset.metadata_info:
            original_path = get_original_file_path(asset.metadata_info)
            if original_path and original_path != asset.file_path and os.path.exists(original_path):
                os.remove(original_path)
    except Exception as exc:
        print(f"Error deleting files for asset {asset_id}: {exc}")

    db.delete(asset)
    db.commit()

    return {"status": "success", "message": f"Asset {asset_id} deleted"}


@router.get("/assets/{asset_id}", response_model=AssetDetailResponse)
def get_asset_detail(asset_id: int, request: Request, db: Session = Depends(get_db)):
    asset = _get_asset_or_404(asset_id, db)
    return build_asset_detail_response(asset)
