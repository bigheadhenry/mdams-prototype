from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import VideoAsset
from ..permissions import CurrentUser, require_permission
from ..schemas import VideoAssetOut

router = APIRouter(prefix="/video", tags=["video"])


@router.get("/resources", response_model=list[VideoAssetOut])
def list_video_assets(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("video.view")),
):
    assets = db.query(VideoAsset).order_by(VideoAsset.created_at.desc(), VideoAsset.id.desc()).all()
    result: list[VideoAssetOut] = []
    for asset in assets:
        layers = asset.metadata_info or {}
        core = layers.get("core") or {}
        result.append(
            VideoAssetOut(
                id=asset.id,
                filename=asset.filename,
                title=str(core.get("title") or asset.filename),
                file_path=asset.file_path,
                file_size=asset.file_size,
                mime_type=asset.mime_type,
                duration_seconds=asset.duration_seconds,
                width=asset.width,
                height=asset.height,
                status=asset.status,
                resource_type=asset.resource_type,
                profile_key=str(core.get("profile_key") or "other"),
                profile_label=str(core.get("profile_label") or "其他"),
                process_message=asset.process_message,
                created_at=asset.created_at,
            )
        )
    return result


@router.get("/resources/{asset_id}", response_model=VideoAssetOut)
def get_video_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("video.view")),
):
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Video asset not found")
    layers = asset.metadata_info or {}
    core = layers.get("core") or {}
    return VideoAssetOut(
        id=asset.id,
        filename=asset.filename,
        title=str(core.get("title") or asset.filename),
        file_path=asset.file_path,
        file_size=asset.file_size,
        mime_type=asset.mime_type,
        duration_seconds=asset.duration_seconds,
        width=asset.width,
        height=asset.height,
        status=asset.status,
        resource_type=asset.resource_type,
        profile_key=str(core.get("profile_key") or "other"),
        profile_label=str(core.get("profile_label") or "其他"),
        process_message=asset.process_message,
        created_at=asset.created_at,
    )


@router.get("/resources/{asset_id}/stream")
def stream_video(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("video.view")),
):
    """Stream video file with range request support."""
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Video asset not found")

    file_path = Path(asset.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    return FileResponse(
        str(file_path),
        media_type=asset.mime_type or "video/mp4",
        filename=asset.filename,
        content_disposition_type="inline",
    )


@router.delete("/resources/{asset_id}")
def delete_video_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("video.delete")),
):
    asset = db.query(VideoAsset).filter(VideoAsset.id == asset_id).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Video asset not found")
    db.delete(asset)
    db.commit()
    return {"ok": True}
