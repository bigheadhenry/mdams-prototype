import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Application, ApplicationItem, Asset
from ..schemas import (
    ApplicationApproveRequest,
    ApplicationCreateRequest,
    ApplicationDetailResponse,
    ApplicationListItem,
)

router = APIRouter(tags=["applications"])


def _build_application_no() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"APP-{stamp}-{uuid4().hex[:6].upper()}"


def _status_label(status: str) -> str:
    return {
        "submitted": "待处理",
        "approved": "已通过",
        "rejected": "已拒绝",
        "fulfilled": "已交付",
    }.get(status, status)


def _to_list_item(application: Application) -> ApplicationListItem:
    return ApplicationListItem(
        id=application.id,
        application_no=application.application_no,
        requester_name=application.requester_name,
        requester_org=application.requester_org,
        purpose=application.purpose,
        usage_scope=application.usage_scope,
        status=application.status,
        status_label=_status_label(application.status),
        review_note=application.review_note,
        item_count=len(application.items),
        created_at=application.created_at,
        submitted_at=application.submitted_at,
        reviewed_at=application.reviewed_at,
    )


def _get_application_or_404(application_id: int, db: Session) -> Application:
    application = (
        db.query(Application)
        .options(joinedload(Application.items).joinedload(ApplicationItem.asset))
        .filter(Application.id == application_id)
        .first()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application


def _build_export_package(application: Application) -> tuple[str, str, str]:
    temp_dir = tempfile.mkdtemp()
    package_root = os.path.join(temp_dir, f"{application.application_no}")
    data_dir = os.path.join(package_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    manifest_items = []
    for item in application.items:
        asset = item.asset
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


@router.post("/applications", response_model=ApplicationDetailResponse)
def create_application(payload: ApplicationCreateRequest, db: Session = Depends(get_db)):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Application must include at least one item")

    asset_ids = [item.asset_id for item in payload.items]
    assets = db.query(Asset).filter(Asset.id.in_(asset_ids)).all()
    asset_map = {asset.id: asset for asset in assets}

    missing_ids = [asset_id for asset_id in asset_ids if asset_id not in asset_map]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Assets not found: {missing_ids}")

    application = Application(
        application_no=_build_application_no(),
        requester_name=payload.requester_name,
        requester_org=payload.requester_org,
        contact_email=payload.contact_email,
        purpose=payload.purpose,
        usage_scope=payload.usage_scope,
        status="submitted",
    )
    db.add(application)
    db.flush()

    for item in payload.items:
        application_item = ApplicationItem(
            application_id=application.id,
            asset_id=item.asset_id,
            requested_variant=item.requested_variant,
            delivery_format=item.delivery_format,
            note=item.note,
        )
        db.add(application_item)

    db.commit()
    db.refresh(application)
    application = _get_application_or_404(application.id, db)
    return application


@router.get("/applications", response_model=list[ApplicationListItem])
def list_applications(db: Session = Depends(get_db)):
    applications = (
        db.query(Application)
        .options(joinedload(Application.items))
        .order_by(Application.created_at.desc(), Application.id.desc())
        .all()
    )
    return [_to_list_item(application) for application in applications]


@router.get("/applications/{application_id}", response_model=ApplicationDetailResponse)
def get_application(application_id: int, db: Session = Depends(get_db)):
    return _get_application_or_404(application_id, db)


@router.post("/applications/{application_id}/approve", response_model=ApplicationDetailResponse)
def approve_application(
    application_id: int,
    payload: ApplicationApproveRequest,
    db: Session = Depends(get_db),
):
    application = _get_application_or_404(application_id, db)
    application.status = "approved"
    application.review_note = payload.review_note
    application.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(application)
    return _get_application_or_404(application_id, db)


@router.post("/applications/{application_id}/reject", response_model=ApplicationDetailResponse)
def reject_application(
    application_id: int,
    payload: ApplicationApproveRequest,
    db: Session = Depends(get_db),
):
    application = _get_application_or_404(application_id, db)
    application.status = "rejected"
    application.review_note = payload.review_note
    application.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(application)
    return _get_application_or_404(application_id, db)


@router.get("/applications/{application_id}/export")
def export_application(
    application_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    application = _get_application_or_404(application_id, db)
    if application.status not in {"approved", "fulfilled"}:
        raise HTTPException(status_code=400, detail="Only approved applications can be exported")

    temp_dir, zip_path, zip_filename = _build_export_package(application)
    background_tasks.add_task(shutil.rmtree, temp_dir)

    application.status = "fulfilled"
    application.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    return FileResponse(zip_path, media_type="application/zip", filename=zip_filename)
