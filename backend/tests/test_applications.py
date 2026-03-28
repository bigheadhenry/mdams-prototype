from datetime import datetime
from pathlib import Path

import pytest
from fastapi import BackgroundTasks

from app.models import Asset
from app.routers import applications as applications_router
from app.schemas import ApplicationApproveRequest, ApplicationCreateItemRequest, ApplicationCreateRequest


pytestmark = [pytest.mark.integration, pytest.mark.contract]


def _create_asset(db_session, name: str) -> Asset:
    asset = Asset(
        filename=name,
        file_path=f"/tmp/{name}",
        file_size=1024,
        mime_type="image/png",
        status="ready",
        resource_type="image_2d_cultural_object",
        metadata_info={"core": {"title": name}},
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def test_create_and_list_applications(db_session):
    asset = _create_asset(db_session, "apply-1.png")

    created = applications_router.create_application(
        ApplicationCreateRequest(
            requester_name="Jing Sun",
            requester_org="Palace Museum",
            contact_email="bigheadhenry@gmail.com",
            purpose="出版配图",
            usage_scope="内部研究",
            items=[
                ApplicationCreateItemRequest(
                    asset_id=asset.id,
                    requested_variant="current",
                    delivery_format="image",
                    note="需要高质量图像",
                )
            ],
        ),
        db=db_session,
    )

    assert created.application_no.startswith("APP-")
    assert created.status == "submitted"
    assert len(created.items) == 1
    assert created.items[0].asset.id == asset.id

    listed = applications_router.list_applications(db=db_session)
    assert len(listed) == 1
    assert listed[0].item_count == 1
    assert listed[0].status_label == "待处理"


def test_approve_application(db_session):
    asset = _create_asset(db_session, "apply-2.png")
    created = applications_router.create_application(
        ApplicationCreateRequest(
            requester_name="Jing Sun",
            purpose="展览申请",
            items=[ApplicationCreateItemRequest(asset_id=asset.id)],
        ),
        db=db_session,
    )

    approved = applications_router.approve_application(
        created.id,
        ApplicationApproveRequest(review_note="可提供衍生图"),
        db=db_session,
    )

    assert approved.status == "approved"
    assert approved.review_note == "可提供衍生图"
    assert isinstance(approved.reviewed_at, datetime)


def test_export_application_marks_fulfilled(tmp_path, db_session):
    source_file = tmp_path / "apply-3.png"
    source_file.write_bytes(b"export-package-test")

    asset = Asset(
        filename="apply-3.png",
        file_path=str(source_file),
        file_size=source_file.stat().st_size,
        mime_type="image/png",
        status="ready",
        resource_type="image_2d_cultural_object",
        metadata_info={"core": {"title": "apply-3.png"}},
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    created = applications_router.create_application(
        ApplicationCreateRequest(
            requester_name="Jing Sun",
            purpose="批量交付",
            items=[ApplicationCreateItemRequest(asset_id=asset.id)],
        ),
        db=db_session,
    )

    applications_router.approve_application(
        created.id,
        ApplicationApproveRequest(review_note="可导出"),
        db=db_session,
    )

    response = applications_router.export_application(
        created.id,
        background_tasks=BackgroundTasks(),
        db=db_session,
    )

    exported_path = Path(response.path)
    assert exported_path.exists()

    refreshed = applications_router.get_application(created.id, db=db_session)
    assert refreshed.status == "fulfilled"
