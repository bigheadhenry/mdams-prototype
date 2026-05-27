import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import BackgroundTasks, UploadFile
from PIL import Image
from starlette.requests import Request

from app import config as app_config
from app.platform import image_source
from app.routers import applications as applications_router
from app.routers import assets as assets_router
from app.routers import iiif as iiif_router
from app.routers import platform as platform_router
from app.schemas import (
    ApplicationApproveRequest,
    ApplicationCreateItemRequest,
    ApplicationCreateRequest,
)


pytestmark = [pytest.mark.integration, pytest.mark.contract]


def _make_png_bytes() -> BytesIO:
    image = Image.new("RGB", (16, 12), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def _make_request(headers=None) -> Request:
    header_items = []
    for key, value in (headers or {}).items():
        header_items.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": header_items,
        "server": ("testserver", 80),
        "client": ("testclient", 50000),
        "scheme": "http",
        "root_path": "",
        "http_version": "1.1",
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    return Request(scope, receive)


async def _upload_demo_asset(db_session, filename: str):
    file = UploadFile(file=_make_png_bytes(), filename=filename)
    return await assets_router.upload_file(file=file, db=db_session)


def test_standard_2d_to_platform_to_application_delivery_flow(db_session, test_upload_dir, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))
    monkeypatch.setattr(app_config, "API_PUBLIC_URL", "http://localhost:3000/api")
    monkeypatch.setattr(app_config, "CANTALOUPE_PUBLIC_URL", "http://localhost:3000/iiif/2")

    uploaded = asyncio.run(_upload_demo_asset(db_session, "standard-demo-flow.png"))
    assert uploaded.status == "ready"
    assert (test_upload_dir / "standard-demo-flow.png").exists()

    asset_detail = assets_router.get_asset_detail(
        asset_id=uploaded.id,
        request=_make_request(),
        db=db_session,
    )
    assert asset_detail.id == uploaded.id
    assert asset_detail.access_paths.preview_enabled is True
    assert asset_detail.output_actions.download_bag is not None

    manifest = iiif_router.get_iiif_manifest(
        asset_id=uploaded.id,
        request=_make_request({"host": "localhost:3000"}),
        db=db_session,
    )
    assert manifest["id"].endswith(f"/iiif/{uploaded.id}/manifest")

    resources_page = platform_router.get_resources(q="standard-demo-flow", db=db_session)
    assert resources_page.total == 1
    unified_resource = resources_page.items[0]
    assert unified_resource.id == f"{image_source.SOURCE_SYSTEM}:{uploaded.id}"
    assert unified_resource.source_system == image_source.SOURCE_SYSTEM
    assert unified_resource.preview_enabled is True

    unified_detail = platform_router.get_resource_by_source(
        source_system=unified_resource.source_system,
        source_id=unified_resource.source_id,
        db=db_session,
    )
    assert unified_detail.id == unified_resource.id
    assert unified_detail.source_record_type == "asset_detail"
    assert unified_detail.source_record["id"] == uploaded.id
    assert next(action for action in unified_detail.actions if action.key == "export_bagit").enabled is True

    application = applications_router.create_application(
        ApplicationCreateRequest(
            requester_name="Standard Demo User",
            requester_org="MDAMS Demo",
            contact_email="demo@example.org",
            purpose="标准演示链路验证",
            usage_scope="内部演示",
            items=[
                ApplicationCreateItemRequest(
                    asset_id=uploaded.id,
                    source_system=unified_detail.source_system,
                    source_id=unified_detail.source_id,
                    resource_type=unified_detail.resource_type,
                    resource_title=unified_detail.title,
                    manifest_url=unified_detail.manifest_url,
                    source_label=unified_detail.source_label,
                    object_number=unified_detail.id,
                    requested_variant="current",
                    delivery_format="image",
                    note="由标准演示主链路测试创建",
                )
            ],
        ),
        db=db_session,
    )
    assert application.status == "submitted"
    assert application.items[0].source_system == image_source.SOURCE_SYSTEM
    assert application.items[0].asset.id == uploaded.id

    approved = applications_router.approve_application(
        application.id,
        ApplicationApproveRequest(review_note="标准演示通过"),
        db=db_session,
    )
    assert approved.status == "approved"

    export_response = applications_router.export_application(
        application.id,
        background_tasks=BackgroundTasks(),
        db=db_session,
    )
    assert export_response.media_type == "application/zip"
    assert Path(export_response.path).exists()

    fulfilled = applications_router.get_application(application.id, db=db_session)
    assert fulfilled.status == "fulfilled"
