from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..models import ThreeDAsset, ThreeDAssetFile
from ..schemas import ThreeDAssetOut, ThreeDDetailResponse
from ..services.three_d_detail import build_three_d_detail_response
from ..services.three_d_metadata import PROFILE_DEFINITIONS, build_three_d_metadata_layers
from ..services.three_d_storage import (
    build_three_d_download_zip,
    build_three_d_package_manifest,
    infer_three_d_role_from_filename,
    normalize_three_d_role,
    pick_primary_three_d_file,
    remove_resource_tree,
    save_three_d_uploads,
    three_d_role_label,
)

router = APIRouter(prefix="/three-d", tags=["three-d"])


def _three_d_dir() -> str:
    return os.path.join(config.UPLOAD_DIR, "three-d")


def _resource_dir(resource_id: int) -> Path:
    return Path(_three_d_dir()) / str(resource_id)


def _get_resource_or_404(resource_id: int, db: Session) -> ThreeDAsset:
    asset = db.query(ThreeDAsset).filter(ThreeDAsset.id == resource_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="3D resource not found")
    return asset


def _normalize_profile_key(profile_key: str | None) -> str | None:
    if not profile_key:
        return None
    normalized = profile_key.strip().lower()
    return normalized if normalized in PROFILE_DEFINITIONS else None


def _upload_filename(upload: UploadFile | None) -> str | None:
    filename = getattr(upload, "filename", None)
    return str(filename) if filename else None


def _coerce_upload_list(value: Sequence[UploadFile] | UploadFile | None) -> list[UploadFile]:
    if value is None:
        return []
    if isinstance(value, UploadFile):
        return [value]
    if isinstance(value, (list, tuple)):
        return [item for item in value if isinstance(item, UploadFile)]
    return []


def _collect_uploads(
    file: UploadFile | None,
    model_files: Sequence[UploadFile] | None,
    point_cloud_files: Sequence[UploadFile] | None,
    oblique_files: Sequence[UploadFile] | None,
) -> dict[str, list[UploadFile]]:
    uploads_by_role: dict[str, list[UploadFile]] = {
        "model": _coerce_upload_list(model_files),
        "point_cloud": _coerce_upload_list(point_cloud_files),
        "oblique_photo": _coerce_upload_list(oblique_files),
    }
    if isinstance(file, UploadFile):
        uploads_by_role.setdefault("model", []).append(file)
    return {role: uploads for role, uploads in uploads_by_role.items() if uploads}


def _determine_profile_and_resource_type(
    *,
    requested_profile_key: str | None,
    uploads_by_role: dict[str, list[UploadFile]],
    fallback_file: UploadFile | None,
) -> tuple[str, str]:
    explicit_profile = _normalize_profile_key(requested_profile_key)
    roles = {normalize_three_d_role(role) for role in uploads_by_role if uploads_by_role.get(role)}
    roles.discard("other")
    if explicit_profile:
        profile_key = explicit_profile
    elif len(roles) > 1:
        profile_key = "package"
    elif len(roles) == 1:
        profile_key = next(iter(roles))
    elif fallback_file is not None:
        profile_key = normalize_three_d_role(infer_three_d_role_from_filename(_upload_filename(fallback_file)))
    else:
        profile_key = "other"

    if profile_key == "package":
        resource_type = "three_d_package"
    elif profile_key == "model":
        resource_type = "three_d_model"
    elif profile_key == "point_cloud":
        resource_type = "three_d_point_cloud"
    elif profile_key == "oblique_photo":
        resource_type = "three_d_oblique_photo"
    else:
        resource_type = "other"

    return profile_key, resource_type


def _serialize_three_d_asset(asset: ThreeDAsset) -> ThreeDAssetOut:
    layers = asset.metadata_info or {}
    core = layers.get("core") if isinstance(layers, dict) else {}
    technical = layers.get("technical") if isinstance(layers, dict) else {}
    files = technical.get("files") if isinstance(technical, dict) else []
    file_roles = []
    if isinstance(files, list):
        for item in files:
            if isinstance(item, dict):
                role = item.get("role")
                if role:
                    file_roles.append(str(role))
    primary_file_role = None
    if isinstance(technical, dict):
        primary_file_role = technical.get("primary_file_role")
    return ThreeDAssetOut(
        id=asset.id,
        resource_group=asset.resource_group,
        filename=asset.filename,
        title=str(core.get("title") or asset.filename),
        file_size=asset.file_size,
        mime_type=asset.mime_type,
        file_count=len(files) if isinstance(files, list) else 0,
        primary_file_role=str(primary_file_role) if primary_file_role else None,
        file_roles=file_roles,
        version_label=str(core.get("version_label") or asset.version_label or "original"),
        version_order=int(core.get("version_order") or asset.version_order or 0),
        is_current=bool(core.get("is_current")) if core.get("is_current") is not None else bool(asset.is_current),
        is_web_preview=bool(core.get("is_web_preview")) if core.get("is_web_preview") is not None else bool(asset.is_web_preview),
        web_preview_status=str(core.get("web_preview_status") or asset.web_preview_status or "disabled"),
        web_preview_reason=str(core.get("web_preview_reason") or asset.web_preview_reason or "") or None,
        status=asset.status,
        resource_type=asset.resource_type,
        profile_key=str(core.get("profile_key") or "other"),
        profile_label=str(core.get("profile_label") or "其他"),
        created_at=asset.created_at,
        process_message=asset.process_message,
    )


@router.post("/upload", response_model=ThreeDAssetOut)
async def upload_three_d_resource(
    file: UploadFile | None = File(None),
    mesh_uploads: list[UploadFile] | None = File(None, alias="model_files"),
    point_cloud_uploads: list[UploadFile] | None = File(None, alias="point_cloud_files"),
    oblique_uploads: list[UploadFile] | None = File(None, alias="oblique_files"),
    title: str | None = Form(None),
    profile_key: str | None = Form(None),
    project_name: str | None = Form(None),
    creator: str | None = Form(None),
    creator_org: str | None = Form(None),
    resource_group: str | None = Form(None),
    version_label: str | None = Form("original"),
    version_order: int | None = Form(0),
    is_current: bool | None = Form(True),
    is_web_preview: bool | None = Form(False),
    web_preview_status: str | None = Form("disabled"),
    web_preview_reason: str | None = Form(None),
    format_name: str | None = Form(None),
    coordinate_system: str | None = Form(None),
    unit: str | None = Form(None),
    vertex_count: int | None = Form(None),
    face_count: int | None = Form(None),
    material_count: int | None = Form(None),
    texture_count: int | None = Form(None),
    point_count: int | None = Form(None),
    lod_count: int | None = Form(None),
    capture_time: str | None = Form(None),
    db: Session = Depends(get_db),
):
    uploads_by_role = _collect_uploads(file, mesh_uploads, point_cloud_uploads, oblique_uploads)
    if not uploads_by_role:
        raise HTTPException(status_code=400, detail="At least one 3D file is required")

    derived_profile_key, resource_type = _determine_profile_and_resource_type(
        requested_profile_key=profile_key,
        uploads_by_role=uploads_by_role,
        fallback_file=file,
    )

    resource_title = title or _upload_filename(file) or "未命名三维资源"
    primary_filename = (
        _upload_filename(file)
        or next((upload.filename for upload in uploads_by_role.get("model", []) if upload.filename), None)
        or next((upload.filename for upload in uploads_by_role.get("point_cloud", []) if upload.filename), None)
        or next((upload.filename for upload in uploads_by_role.get("oblique_photo", []) if upload.filename), None)
        or resource_title
    )

    db_asset = ThreeDAsset(
        resource_group=resource_group or title or resource_title,
        filename=str(primary_filename),
        file_path="",
        file_size=0,
        mime_type=None,
        status="processing",
        resource_type=resource_type,
        process_message="三维资源正在入库处理中",
        version_label=(version_label or "original").strip() or "original",
        version_order=int(version_order or 0),
        is_current=bool(is_current) if is_current is not None else True,
        is_web_preview=bool(is_web_preview) if is_web_preview is not None else False,
        web_preview_status=(web_preview_status or "disabled").strip() or "disabled",
        web_preview_reason=web_preview_reason,
        metadata_info={},
    )
    db.add(db_asset)
    db.commit()
    db.refresh(db_asset)

    resource_dir = _resource_dir(db_asset.id)
    resource_dir.mkdir(parents=True, exist_ok=True)

    saved_files = await save_three_d_uploads(resource_dir, uploads_by_role)
    if not saved_files:
        db.delete(db_asset)
        db.commit()
        raise HTTPException(status_code=400, detail="No 3D files were saved")

    primary_file = pick_primary_three_d_file(saved_files) or saved_files[0]
    for file_record in saved_files:
        file_record["is_primary"] = file_record["actual_filename"] == primary_file["actual_filename"] and file_record["role"] == primary_file["role"]

    total_file_size = sum(int(file_record.get("file_size") or 0) for file_record in saved_files)
    resource_type = resource_type if derived_profile_key != "other" else resource_type
    metadata_layers = build_three_d_metadata_layers(
        asset_id=db_asset.id,
        asset_filename=primary_file["filename"],
        asset_file_path=str(primary_file["file_path"]),
        asset_file_size=total_file_size,
        asset_mime_type=primary_file.get("mime_type"),
        asset_status="ready",
        asset_resource_type=resource_type,
        metadata={
            "title": resource_title,
            "three_d_profile": derived_profile_key,
            "project_name": project_name,
            "creator": creator,
            "creator_org": creator_org,
            "format_name": format_name,
            "coordinate_system": coordinate_system,
            "unit": unit,
            "vertex_count": vertex_count,
            "face_count": face_count,
            "material_count": material_count,
            "texture_count": texture_count,
            "point_count": point_count,
            "lod_count": lod_count,
            "capture_time": capture_time,
            "resource_group": db_asset.resource_group,
            "version_label": db_asset.version_label,
            "version_order": db_asset.version_order,
            "is_current": db_asset.is_current,
            "is_web_preview": db_asset.is_web_preview,
            "web_preview_status": db_asset.web_preview_status,
            "web_preview_reason": db_asset.web_preview_reason,
            "ingest_method": "upload",
            "file_count": len(saved_files),
            "role_summary": ", ".join(f"{three_d_role_label(item['role'])}" for item in saved_files),
            "file_name": primary_file["filename"],
            "file_size": total_file_size,
        },
        source_metadata={
            "files": saved_files,
            "profile_key": derived_profile_key,
            "title": resource_title,
            "project_name": project_name,
            "creator": creator,
            "creator_org": creator_org,
            "format_name": format_name,
            "coordinate_system": coordinate_system,
            "unit": unit,
        },
        profile_hint=derived_profile_key,
        file_records=saved_files,
    )

    manifest_path = build_three_d_package_manifest(resource_dir, asset=db_asset, metadata_layers=metadata_layers, file_records=saved_files)
    db_asset.filename = str(primary_file["filename"] or resource_title)
    db_asset.file_path = str(manifest_path)
    db_asset.file_size = total_file_size
    db_asset.mime_type = "application/json" if len(saved_files) > 1 else (primary_file.get("mime_type") or "application/octet-stream")
    db_asset.status = "ready"
    db_asset.resource_type = resource_type
    db_asset.process_message = "三维资源已上传并完成基础登记"
    db_asset.metadata_info = metadata_layers
    db_asset.version_label = (version_label or "original").strip() or "original"
    db_asset.version_order = int(version_order or 0)
    db_asset.is_current = bool(is_current) if is_current is not None else True
    db_asset.is_web_preview = bool(is_web_preview) if is_web_preview is not None else False
    db_asset.web_preview_status = (web_preview_status or "disabled").strip() or "disabled"
    db_asset.web_preview_reason = web_preview_reason
    db.add(db_asset)

    db.query(ThreeDAssetFile).filter(ThreeDAssetFile.asset_id == db_asset.id).delete()
    for sort_order, file_record in enumerate(saved_files):
        db.add(
            ThreeDAssetFile(
                asset_id=db_asset.id,
                role=str(file_record.get("role") or "other"),
                role_label=str(file_record.get("role_label") or "其他"),
                filename=str(file_record.get("filename") or ""),
                actual_filename=str(file_record.get("actual_filename") or ""),
                file_path=str(file_record.get("file_path") or ""),
                file_size=int(file_record.get("file_size") or 0),
                mime_type=file_record.get("mime_type"),
                sort_order=sort_order,
                is_primary=bool(file_record.get("is_primary")),
            )
        )

    db.commit()
    db.refresh(db_asset)
    return _serialize_three_d_asset(db_asset)


@router.get("/resources", response_model=list[ThreeDAssetOut])
def list_three_d_resources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    assets = db.query(ThreeDAsset).order_by(ThreeDAsset.created_at.desc(), ThreeDAsset.id.desc()).offset(skip).limit(limit).all()
    return [_serialize_three_d_asset(asset) for asset in assets]


@router.get("/resources/{resource_id}", response_model=ThreeDDetailResponse)
def get_three_d_resource(resource_id: int, db: Session = Depends(get_db)):
    asset = _get_resource_or_404(resource_id, db)
    return build_three_d_detail_response(asset)


@router.get("/resources/{resource_id}/download")
def download_three_d_resource(resource_id: int, db: Session = Depends(get_db)):
    asset = _get_resource_or_404(resource_id, db)
    resource_dir = _resource_dir(asset.id)
    file_records = list(asset.files or [])
    if not file_records:
        raise HTTPException(status_code=404, detail="3D resource files not found")
    if len(file_records) == 1:
        file_path = Path(file_records[0].file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        return FileResponse(path=str(file_path), filename=file_records[0].filename)

    zip_path = build_three_d_download_zip(resource_dir, f"three-d-{asset.id}.zip", [file.__dict__ for file in file_records])
    return FileResponse(path=str(zip_path), filename=f"three-d-{asset.id}.zip", media_type="application/zip")


@router.get("/resources/{resource_id}/files/{file_id}")
def download_three_d_resource_file(resource_id: int, file_id: int, db: Session = Depends(get_db)):
    asset = _get_resource_or_404(resource_id, db)
    file_record = next((record for record in asset.files if record.id == file_id), None)
    if file_record is None:
        raise HTTPException(status_code=404, detail="3D file not found")
    file_path = Path(file_record.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=str(file_path),
        filename=file_record.actual_filename or file_record.filename,
        media_type=file_record.mime_type or "application/octet-stream",
    )


@router.delete("/resources/{resource_id}")
def delete_three_d_resource(resource_id: int, db: Session = Depends(get_db)):
    asset = _get_resource_or_404(resource_id, db)
    remove_resource_tree(_resource_dir(asset.id))
    db.delete(asset)
    db.commit()
    return {"status": "success", "message": f"3D resource {resource_id} deleted"}
