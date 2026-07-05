import json
import zipfile
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import BackgroundTasks

from app.models import Asset, ApplicationAuditLog
from app.permissions import CurrentUser
from app.routers import applications as applications_router
from app.schemas import ApplicationApproveRequest, ApplicationCreateItemRequest, ApplicationCreateRequest


pytestmark = [pytest.mark.integration, pytest.mark.contract]


# Reusable mock users for tests that require authentication
CREATOR = CurrentUser(
    user_id="resource_user",
    display_name="申请者",
    roles={"resource_user"},
    permissions={"application.create"},
    collection_scope=set(),
)

REVIEWER = CurrentUser(
    user_id="application_reviewer",
    display_name="审批员",
    roles={"application_reviewer"},
    permissions={"application.review", "application.export"},
    collection_scope=set(),
)


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
            requester_name="孙竞",
            requester_org="故宫博物院",
            contact_email="test@example.com",
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
        current_user=CREATOR,
    )

    assert created.application_no.startswith("APP-")
    assert created.status == "submitted"
    assert len(created.items) == 1
    assert created.items[0].asset.id == asset.id

    listed = applications_router.list_applications(db=db_session)
    assert len(listed) == 1
    assert listed[0].item_count == 1
    assert listed[0].status_label == "待处理"

    # Verify audit log: submitted
    assert len(created.audit_logs) == 1
    assert created.audit_logs[0].action == "submitted"
    assert created.audit_logs[0].actor_display_name == "申请者"


def test_approve_application(db_session):
    asset = _create_asset(db_session, "apply-2.png")
    created = applications_router.create_application(
        ApplicationCreateRequest(
            requester_name="孙竞",
            purpose="展览申请",
            items=[ApplicationCreateItemRequest(asset_id=asset.id)],
        ),
        db=db_session,
        current_user=CREATOR,
    )

    approved = applications_router.approve_application(
        created.id,
        ApplicationApproveRequest(review_note="可提供衍生图"),
        db=db_session,
        current_user=REVIEWER,
    )

    assert approved.status == "approved"
    assert approved.review_note == "可提供衍生图"
    assert isinstance(approved.reviewed_at, datetime)
    assert approved.reviewed_by == "审批员"

    # Verify audit log: submitted + approved
    assert len(approved.audit_logs) == 2
    assert approved.audit_logs[0].action == "submitted"
    assert approved.audit_logs[1].action == "approved"
    assert approved.audit_logs[1].actor_display_name == "审批员"
    assert approved.audit_logs[1].review_note == "可提供衍生图"


def test_reject_application(db_session):
    asset = _create_asset(db_session, "apply-reject.png")
    created = applications_router.create_application(
        ApplicationCreateRequest(
            requester_name="孙竞",
            purpose="外部出版",
            items=[ApplicationCreateItemRequest(asset_id=asset.id)],
        ),
        db=db_session,
        current_user=CREATOR,
    )

    rejected = applications_router.reject_application(
        created.id,
        ApplicationApproveRequest(review_note="用途不符合规定"),
        db=db_session,
        current_user=REVIEWER,
    )

    assert rejected.status == "rejected"
    assert rejected.review_note == "用途不符合规定"
    assert isinstance(rejected.reviewed_at, datetime)
    assert rejected.reviewed_by == "审批员"

    # Verify audit log: submitted + rejected
    assert len(rejected.audit_logs) == 2
    assert rejected.audit_logs[0].action == "submitted"
    assert rejected.audit_logs[1].action == "rejected"
    assert rejected.audit_logs[1].review_note == "用途不符合规定"


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
            requester_name="孙竞",
            purpose="批量交付",
            items=[ApplicationCreateItemRequest(asset_id=asset.id)],
        ),
        db=db_session,
        current_user=CREATOR,
    )

    applications_router.approve_application(
        created.id,
        ApplicationApproveRequest(review_note="可导出"),
        db=db_session,
        current_user=REVIEWER,
    )

    response = applications_router.export_application(
        created.id,
        background_tasks=BackgroundTasks(),
        db=db_session,
        current_user=REVIEWER,
    )

    exported_path = Path(response.path)
    assert exported_path.exists()

    refreshed = applications_router.get_application(created.id, db=db_session)
    assert refreshed.status == "fulfilled"

    # Verify audit log: submitted + approved + exported
    assert len(refreshed.audit_logs) == 3
    assert refreshed.audit_logs[0].action == "submitted"
    assert refreshed.audit_logs[1].action == "approved"
    assert refreshed.audit_logs[2].action == "exported"
    assert refreshed.audit_logs[2].actor_display_name == "审批员"

    # --- Verify delivery package contents ---
    with zipfile.ZipFile(exported_path, "r") as zf:
        namelist = zf.namelist()

        auth_files = [n for n in namelist if "授权说明" in n]
        assert len(auth_files) == 1, f"Missing 授权说明.md in zip: {namelist}"
        auth_content = zf.read(auth_files[0]).decode("utf-8")
        assert "授权编号" in auth_content
        assert created.application_no in auth_content
        assert "批量交付" in auth_content
        assert "署名要求" in auth_content
        assert "故宫博物院" in auth_content

        json_files = [n for n in namelist if n.endswith("application.json")]
        assert len(json_files) == 1
        app_data = json.loads(zf.read(json_files[0]).decode("utf-8"))
        assert app_data["application_no"] == created.application_no
        assert app_data["purpose"] == "批量交付"
        assert app_data["reviewed_at"] is not None
        assert len(app_data["items"]) == 1

        data_files = [n for n in namelist if n.startswith(f"{created.application_no}/data/")]
        assert len(data_files) >= 1

        readme_files = [n for n in namelist if n.endswith("README.txt")]
        assert len(readme_files) == 1
