import json
import zipfile
from datetime import datetime
from pathlib import Path

import pytest
from fastapi import BackgroundTasks

from app.models import Asset, ApplicationAuditLog, ResourceEvent, ThreeDAsset, ThreeDAssetFile, ThreeDDigitalObject
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


def test_mixed_image_and_three_d_application_delivers_physical_files(tmp_path, db_session):
    image_path = tmp_path / "image.tif"
    image_path.write_bytes(b"image-master")
    image = Asset(
        filename=image_path.name,
        file_path=str(image_path),
        file_size=image_path.stat().st_size,
        mime_type="image/tiff",
        status="ready",
        resource_type="image_2d_cultural_object",
        metadata_info={"core": {"title": "二维原件"}, "technical": {"original_file_path": str(image_path)}},
    )
    digital_object = ThreeDDigitalObject(object_key="delivery-object", title="三维对象", lifecycle_status="published")
    db_session.add_all([image, digital_object])
    db_session.flush()
    model_path = tmp_path / "model.glb"
    model_path.write_bytes(b"glTF-delivery")
    representation = ThreeDAsset(
        three_d_object_id=digital_object.id,
        filename=model_path.name,
        file_path=str(tmp_path / "manifest.json"),
        file_size=model_path.stat().st_size,
        mime_type="model/gltf-binary",
        status="ready",
        resource_type="three_d_model",
        version_label="v1",
        representation_type="web_display",
        publication_status="published",
        is_current=True,
        is_web_preview=True,
        web_preview_status="ready",
        metadata_info={"core": {"title": "三维表现"}},
    )
    db_session.add(representation)
    db_session.flush()
    db_session.add(
        ThreeDAssetFile(
            asset_id=representation.id,
            role="model",
            role_label="模型",
            filename=model_path.name,
            actual_filename=model_path.name,
            file_path=str(model_path),
            file_size=model_path.stat().st_size,
            mime_type="model/gltf-binary",
            is_primary=True,
        )
    )
    db_session.commit()

    created = applications_router.create_application(
        ApplicationCreateRequest(
            requester_name="混合资源申请人",
            purpose="展览",
            items=[
                ApplicationCreateItemRequest(asset_id=image.id, source_system="image_2d", source_id=str(image.id), requested_variant="current"),
                ApplicationCreateItemRequest(source_system="three_d", source_id=str(representation.id), resource_type="three_d_model", delivery_format="3d_package"),
            ],
        ),
        db=db_session,
        current_user=CREATOR,
    )
    applications_router.approve_application(created.id, ApplicationApproveRequest(review_note="通过"), db=db_session, current_user=REVIEWER)
    response = applications_router.export_application(created.id, BackgroundTasks(), db=db_session, current_user=REVIEWER)

    with zipfile.ZipFile(response.path) as package:
        names = package.namelist()
        assert any("data/image_2d/" in name and name.endswith("image.tif") for name in names)
        assert any("data/three_d/" in name and name.endswith("model.glb") for name in names)
        checksum_name = next(name for name in names if name.endswith("manifest-sha256.txt"))
        checksum_text = package.read(checksum_name).decode("utf-8")
        assert "image.tif" in checksum_text
        assert "model.glb" in checksum_text
    assert db_session.query(ResourceEvent).filter(ResourceEvent.event_type == "export").count() == 2
