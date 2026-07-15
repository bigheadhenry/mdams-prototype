import os
from pathlib import Path

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..models import Asset, ImageRecord
from ..permissions import CurrentUser, can_access_visibility_scope, ensure_current_user, require_permission
from ..schemas import AssetDetailResponse, AssetOut
from ..services.asset_detail import build_asset_detail_response
from ..services.iiif_access import (
    get_asset_iiif_access_file_path,
    get_asset_original_file_path,
    mark_asset_derivative_pending,
    mark_asset_ready_with_original_access,
)
from ..services.metadata_layers import build_metadata_layers, get_original_file_path
from ..services.preview_images import ensure_preview_image
from ..services.fixity import calculate_sha256, verify_path
from ..services.resource_access import assert_asset_visible
from ..services.resource_events import record_resource_event
from ..tasks import generate_iiif_access_derivative

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


def _safe_upload_filename(filename: str | None) -> str:
    safe_name = Path((filename or "upload.bin").replace("\\", "/")).name
    if safe_name in {"", ".", ".."}:
        return "upload.bin"
    return safe_name


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

    safe_filename = _safe_upload_filename(file.filename)
    file_location = os.path.join(config.UPLOAD_DIR, safe_filename)
    os.makedirs(os.path.dirname(file_location), exist_ok=True)

    chunk_size = 64 * 1024
    with open(file_location, "wb") as buffer:
        while content := await file.read(chunk_size):
            buffer.write(content)

    file_size = os.path.getsize(file_location)
    fixity_sha256 = calculate_sha256(file_location)
    width, height = 0, 0
    try:
        with Image.open(file_location) as img:
            width, height = img.size
    except Exception:
        pass

    db_asset = Asset(
        filename=safe_filename,
        file_path=file_location,
        file_size=file_size,
        mime_type=file.content_type,
        visibility_scope=normalized_visibility_scope,
        collection_object_id=normalized_collection_object_id,
        status="processing",
        resource_type="image_2d_cultural_object",
        process_message="Asset upload received.",
        metadata_info=build_metadata_layers(
            asset_filename=safe_filename,
            asset_file_path=file_location,
            asset_file_size=file_size,
            asset_mime_type=file.content_type,
            asset_status="processing",
            asset_resource_type="image_2d_cultural_object",
            asset_visibility_scope=normalized_visibility_scope,
            asset_collection_object_id=normalized_collection_object_id,
            metadata={
                "width": width,
                "height": height,
                "ingest_method": "upload",
                "original_file_name": safe_filename,
                "image_file_name": os.path.basename(file_location),
                "file_size": file_size,
                "format_name": file.content_type,
                "fixity_sha256": fixity_sha256,
                "fixity_status": "verified",
                "last_verified_at": datetime.now(timezone.utc).isoformat(),
                "visibility_scope": normalized_visibility_scope,
                "collection_object_id": normalized_collection_object_id,
            },
            source_metadata={
                "ingest_method": "upload",
                "file_name": safe_filename,
                "file_size": file_size,
                "visibility_scope": normalized_visibility_scope,
                "collection_object_id": normalized_collection_object_id,
            },
        ),
    )

    if get_asset_iiif_access_file_path(db_asset, allow_original_fallback=False):
        mark_asset_ready_with_original_access(db_asset)
    else:
        mark_asset_derivative_pending(db_asset)

    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)
    record_resource_event(
        db,
        source_system="image_2d",
        source_id=db_asset.id,
        event_type="ingest",
        status="completed",
        actor=ensure_current_user(_user),
        description="2D asset uploaded and baseline checksum recorded",
        evidence=fixity_sha256,
    )
    db.commit()

    if db_asset.status == "processing":
        generate_iiif_access_derivative.delay(db_asset.id, file_location)

    return db_asset


@router.get("/debug/files")
def list_uploaded_files(
    _user=Depends(require_permission("system.manage")),
):
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
    user: CurrentUser = Depends(require_permission("image.delete")),
):
    asset = _get_asset_or_404(asset_id, db)
    assert_asset_visible(asset, user)

    try:
        removable_paths = {
            asset.file_path,
            get_original_file_path(asset.metadata_info),
            get_asset_original_file_path(asset),
            get_asset_iiif_access_file_path(asset, allow_original_fallback=False, require_exists=False),
        }
        metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
        technical = metadata.get("technical") if isinstance(metadata, dict) else {}
        if isinstance(technical, dict):
            removable_paths.add(technical.get("preview_image_path"))

        for removable_path in removable_paths:
            if isinstance(removable_path, str) and removable_path and os.path.exists(removable_path):
                os.remove(removable_path)
    except Exception as exc:
        print(f"Error deleting files for asset {asset_id}: {exc}")

    db.delete(asset)
    db.commit()

    return {"status": "success", "message": f"Asset {asset_id} deleted"}


def _asset_technical(asset: Asset) -> dict[str, object]:
    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    technical = metadata.get("technical") if isinstance(metadata, dict) else {}
    return dict(technical) if isinstance(technical, dict) else {}


@router.get("/assets/operations/summary")
def get_asset_operations_summary(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.view")),
):
    assets = [asset for asset in db.query(Asset).all() if _is_asset_visible_to_user(asset, user)]
    can_list_all_records = user.has_permission("image.record.list")
    can_view_ready_records = user.has_permission("image.record.view_ready_for_upload")
    hashes: dict[str, int] = {}
    for asset in assets:
        checksum = str(_asset_technical(asset).get("fixity_sha256") or "")
        if checksum:
            hashes[checksum] = hashes.get(checksum, 0) + 1
    return {
        "total": len(assets),
        "processing": sum(asset.status == "processing" for asset in assets),
        "failed": sum(asset.status == "error" for asset in assets),
        "iiif_not_ready": sum(not bool(get_asset_iiif_access_file_path(asset, require_exists=True)) for asset in assets),
        "fixity_attention": sum(str(_asset_technical(asset).get("fixity_status") or "pending") not in {"verified", "recorded"} for asset in assets),
        "ready_for_upload": (
            db.query(ImageRecord).filter(ImageRecord.status == "ready_for_upload").count()
            if can_list_all_records or can_view_ready_records
            else 0
        ),
        "pending_validation": (
            db.query(ImageRecord).filter(ImageRecord.status == "uploaded_pending_validation").count()
            if can_list_all_records
            else 0
        ),
        "duplicate_files": sum(count - 1 for count in hashes.values() if count > 1),
    }


@router.post("/assets/{asset_id}/verify-fixity")
def verify_asset_fixity(
    asset_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.edit")),
):
    asset = _get_asset_or_404(asset_id, db)
    assert_asset_visible(asset, user)
    technical = _asset_technical(asset)
    path = get_asset_original_file_path(asset) or asset.file_path
    outcome = verify_path(path, str(technical.get("fixity_sha256") or "") or None)
    technical["fixity_sha256"] = outcome.expected_sha256
    technical["fixity_status"] = outcome.status
    technical["last_verified_at"] = outcome.verified_at.isoformat()
    metadata = asset.metadata_info if isinstance(asset.metadata_info, dict) else {}
    metadata["technical"] = technical
    asset.metadata_info = metadata
    record_resource_event(
        db,
        source_system="image_2d",
        source_id=asset.id,
        event_type="preserve",
        status=outcome.status,
        actor=user,
        description=outcome.message,
        evidence=outcome.actual_sha256,
    )
    db.commit()
    return {
        "asset_id": asset.id,
        "expected_sha256": outcome.expected_sha256,
        "actual_sha256": outcome.actual_sha256,
        "status": outcome.status,
        "verified_at": outcome.verified_at,
        "message": outcome.message,
    }


@router.post("/assets/operations/verify-fixity")
def verify_assets_fixity_batch(
    asset_ids: list[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.edit")),
):
    results = []
    for asset_id in asset_ids:
        results.append(verify_asset_fixity(asset_id, db, user))
    return {"results": results}


@router.post("/assets/operations/regenerate-derivatives")
def regenerate_asset_derivatives_batch(
    asset_ids: list[int] = Body(..., embed=True),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.edit")),
):
    queued = []
    for asset_id in asset_ids:
        asset = _get_asset_or_404(asset_id, db)
        assert_asset_visible(asset, user)
        original_path = get_asset_original_file_path(asset)
        if not original_path:
            continue
        mark_asset_derivative_pending(asset)
        generate_iiif_access_derivative.delay(asset.id, original_path)
        queued.append(asset.id)
    db.commit()
    return {"queued_asset_ids": queued}


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


@router.get("/assets/{asset_id}/preview")
def get_asset_preview(
    asset_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("image.view")),
):
    asset = _get_asset_or_404(asset_id, db)
    user = ensure_current_user(user)
    if not _is_asset_visible_to_user(asset, user):
        raise HTTPException(status_code=403, detail="Asset is not visible to current user")

    preview_path = ensure_preview_image(asset)
    if not preview_path:
        raise HTTPException(status_code=404, detail="Preview image not available")

    return FileResponse(
        preview_path,
        media_type="image/jpeg",
        filename=os.path.basename(preview_path),
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )
