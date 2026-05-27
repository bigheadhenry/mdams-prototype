import shutil
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Application, ApplicationItem, Asset
from ..permissions import CurrentUser, ensure_current_user, require_any_permission, require_permission
from ..services.application_delivery import build_application_export_package
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


@router.post("/applications", response_model=ApplicationDetailResponse)
def create_application(
    payload: ApplicationCreateRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("application.create")),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Application must include at least one item")

    asset_ids = [item.asset_id for item in payload.items if item.asset_id is not None]
    assets = db.query(Asset).filter(Asset.id.in_(asset_ids)).all() if asset_ids else []
    asset_map = {asset.id: asset for asset in assets}

    missing_ids = [asset_id for asset_id in asset_ids if asset_id not in asset_map]
    if missing_ids:
        raise HTTPException(status_code=404, detail=f"Assets not found: {missing_ids}")

    invalid_items = [
        index + 1
        for index, item in enumerate(payload.items)
        if item.asset_id is None and not (item.source_system and item.source_id)
    ]
    if invalid_items:
        raise HTTPException(status_code=400, detail=f"Application items missing unified resource locator: {invalid_items}")

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
            source_system=item.source_system or ("image_2d" if item.asset_id is not None else None),
            source_id=item.source_id or (str(item.asset_id) if item.asset_id is not None else None),
            resource_type=item.resource_type,
            resource_title=item.resource_title,
            manifest_url=item.manifest_url,
            source_label=item.source_label,
            object_number=item.object_number,
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
def list_applications(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_any_permission("application.view_all", "application.view_own")),
):
    user = ensure_current_user(user)
    applications = (
        db.query(Application)
        .options(joinedload(Application.items))
        .order_by(Application.created_at.desc(), Application.id.desc())
        .all()
    )
    return [_to_list_item(application) for application in applications]


@router.get("/applications/{application_id}", response_model=ApplicationDetailResponse)
def get_application(
    application_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_any_permission("application.view_all", "application.view_own")),
):
    user = ensure_current_user(user)
    application = _get_application_or_404(application_id, db)
    return application


@router.post("/applications/{application_id}/approve", response_model=ApplicationDetailResponse)
def approve_application(
    application_id: int,
    payload: ApplicationApproveRequest,
    db: Session = Depends(get_db),
    _user=Depends(require_permission("application.review")),
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
    _user=Depends(require_permission("application.review")),
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
    _user=Depends(require_permission("application.export")),
):
    application = _get_application_or_404(application_id, db)
    if application.status not in {"approved", "fulfilled"}:
        raise HTTPException(status_code=400, detail="Only approved applications can be exported")

    temp_dir, zip_path, zip_filename = build_application_export_package(application)
    background_tasks.add_task(shutil.rmtree, temp_dir)

    application.status = "fulfilled"
    application.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    return FileResponse(zip_path, media_type="application/zip", filename=zip_filename)
