import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import BackgroundTasks, UploadFile
from PIL import Image
from starlette.requests import Request

from app.models import Asset
from app import config as app_config
from app.schemas import AssetDetailResponse
from app.routers import assets as assets_router
from app.routers import downloads as downloads_router
from app.routers import iiif as iiif_router
from app.routers import health as health_router


pytestmark = [pytest.mark.smoke, pytest.mark.integration]


def _make_png_bytes():
    image = Image.new("RGB", (8, 8), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def _make_request(headers=None):
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


async def _upload_sample(db_session, upload_dir):
    file = UploadFile(file=_make_png_bytes(), filename="smoke.png")
    uploaded = await assets_router.upload_file(file=file, db=db_session)

    saved_file = upload_dir / "smoke.png"
    assert saved_file.exists()
    assert uploaded.filename == "smoke.png"
    assert uploaded.status == "ready"
    return uploaded


def test_root_health_and_upload_chain(db_session, test_upload_dir, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))

    root_response = assets_router.read_root()
    assert root_response["message"] == "Welcome to MEAM Prototype API"

    health_payload = health_router.build_health_payload(db_session)
    assert health_payload["status"] == "healthy"
    assert health_payload["checks"]["database"]["status"] == "healthy"
    assert health_payload["checks"]["upload_dir"]["status"] == "healthy"

    uploaded = asyncio.run(_upload_sample(db_session, test_upload_dir))

    assets = assets_router.list_assets(db=db_session)
    assert len(assets) == 1
    assert assets[0].filename == "smoke.png"

    detail = assets_router.get_asset_detail(asset_id=uploaded.id, request=_make_request(), db=db_session)
    assert detail.id == uploaded.id
    assert detail.status == "ready"
    assert detail.access_paths.preview_enabled is True
    detail_schema = AssetDetailResponse.model_validate(detail.model_dump())
    assert detail_schema.file.actual_filename == "smoke.png"
    assert detail_schema.status_info.preview_ready is True
    assert detail_schema.lifecycle[0].step == "object_created"
    assert detail_schema.lifecycle[0].timestamp is not None
    assert any(item.step == "preview_ready" for item in detail_schema.lifecycle)
    assert detail_schema.process_timeline[0].step == "object_created"
    assert detail_schema.process_timeline[-1].step == "output_ready"
    assert detail_schema.structure.primary_file.is_current is True
    assert detail_schema.structure.packaging is not None
    assert detail_schema.output_actions.download_bag is not None
    assert detail_schema.metadata_layers["schema_version"] == "2.0"
    assert detail_schema.metadata_layers["profile"]["key"] == "other"
    assert detail_schema.metadata_layers["technical"]["width"] == 8
    assert detail_schema.metadata_layers["technical"]["height"] == 8

    manifest = iiif_router.get_iiif_manifest(
        asset_id=uploaded.id,
        request=_make_request({"host": "localhost:3000"}),
        db=db_session,
    )
    assert manifest["id"].endswith(f"/iiif/{uploaded.id}/manifest")
    assert manifest["items"][0]["id"].endswith(f"/iiif/{uploaded.id}/canvas/1")

    download_response = downloads_router.download_asset_file(asset_id=uploaded.id, db=db_session)
    assert Path(download_response.path).exists()

    download_bag_response = downloads_router.download_asset_bag(
        asset_id=uploaded.id,
        background_tasks=BackgroundTasks(),
        db=db_session,
    )
    assert download_bag_response.media_type == "application/zip"
    assert Path(download_bag_response.path).exists()

    db_session.query(Asset).delete()
    db_session.commit()
