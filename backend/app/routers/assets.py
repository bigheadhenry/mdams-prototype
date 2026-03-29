import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from PIL import Image
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..models import Asset
from ..permissions import CurrentUser, can_access_visibility_scope, ensure_current_user, require_permission
from ..schemas import AssetDetailResponse, AssetOut
from ..services.asset_detail import build_asset_detail_response
from ..services.metadata_layers import build_metadata_layers, get_original_file_path

router = APIRouter(tags=["assets"])


@router.get("/")
def read_root():
    return {"message": "Welcome to MEAM Prototype API"}


def _normalize_visibility_scope(value: object) -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"open", "owner_only"}:
            return normalized
    return "open"


def _normalize_collection_object_id(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
    return None


@router.post("/upload", response_model=AssetOut)
async def upload_file(
    file: UploadFile = File(...),
    visibility_scope: str | None = Form("open"),
    collection_object_id: int | None = Form(None),
    db: Session = Depends(get_db),
    _user=Depends(require_permission("image.upload")),
):
    normalized_visibility_scope = _normalize_visibility_scope(visibility_scope)
    normalized_collection_object_id = _normalize_collection_object_id(collection_object_id)

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
        visibility_scope=normalized_visibility_scope,
        collection_object_id=normalized_collection_object_id,
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
            asset_visibility_scope=normalized_visibility_scope,
            asset_collection_object_id=normalized_collection_object_id,
            metadata={
                "width": width,
                "height": height,
                "ingest_method": "upload",
                "original_file_name": file.filename,
                "image_file_name": os.path.basename(file_location),
                "file_size": file_size,
                "format_name": file.content_type,
                "visibility_scope": normalized_visibility_scope,
                "collection_object_id": normalized_collection_object_id,
            },
            source_metadata={
                "ingest_method": "upload",
                "file_name": file.filename,
                "file_size": file_size,
                "visibility_scope": normalized_visibility_scope,
                "collection_object_id": normalized_collection_object_id,
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


def _asset_visibility_scope(asset: Asset) -> str:
    visibility_scope = getattr(asset, "visibility_scope", None)
    if visibility_scope:
        return str(visibility_scope)
    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    core = metadata.get("core") if isinstance(metadata, dict) else {}
    if isinstance(core, dict):
        core_scope = core.get("visibility_scope")
        if core_scope not in (None, ""):
            return str(core_scope)
    return "open"


def _asset_collection_object_id(asset: Asset) -> int | None:
    collection_object_id = getattr(asset, "collection_object_id", None)
    if isinstance(collection_object_id, bool):
        return int(collection_object_id)
    if isinstance(collection_object_id, int):
        return collection_object_id
    if isinstance(collection_object_id, str) and collection_object_id.isdigit():
        return int(collection_object_id)
    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    core = metadata.get("core") if isinstance(metadata, dict) else {}
    if isinstance(core, dict):
        core_collection_object_id = core.get("collection_object_id")
        if isinstance(core_collection_object_id, int):
            return core_collection_object_id
        if isinstance(core_collection_object_id, str) and core_collection_object_id.isdigit():
            return int(core_collection_object_id)
    return None


def _is_asset_visible_to_user(asset: Asset, user: CurrentUser) -> bool:
    return can_access_visibility_scope(
        user,
        visibility_scope=_asset_visibility_scope(asset),
        collection_object_id=_asset_collection_object_id(asset),
    )


@router.get("/assets", response_model=list[AssetOut])
def list_assets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.view")),
):
    user = ensure_current_user(user)
    assets = db.query(Asset).order_by(Asset.created_at.desc(), Asset.id.desc()).all()
    visible_assets = [asset for asset in assets if _is_asset_visible_to_user(asset, user)]
    return visible_assets[skip : skip + limit]


@router.delete("/assets/{asset_id}")
def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("image.delete")),
):
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
def get_asset_detail(
    asset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.view")),
):
    asset = _get_asset_or_404(asset_id, db)
    user = ensure_current_user(user)
    if not _is_asset_visible_to_user(asset, user):
        raise HTTPException(status_code=403, detail="Asset is not visible to current user")
    return build_asset_detail_response(asset)
