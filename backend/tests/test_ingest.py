import asyncio
import hashlib
import json
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from PIL import Image

from app import config as app_config
from app.models import Asset
from app.routers import ingest as ingest_router


pytestmark = [pytest.mark.integration, pytest.mark.contract]


def _make_png_bytes(color="white"):
    image = Image.new("RGB", (8, 8), color=color)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def test_ingest_sip_persists_asset_and_returns_fixity(monkeypatch, db_session, test_upload_dir):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))
    monkeypatch.setattr(ingest_router, "extract_metadata", lambda _path: {"File": {"ImageWidth": 8, "ImageHeight": 8}})
    queued: list[tuple[int, str]] = []
    monkeypatch.setattr(
        ingest_router.generate_iiif_access_derivative,
        "delay",
        lambda asset_id, file_path: queued.append((asset_id, file_path)),
    )

    file_buffer = _make_png_bytes()
    payload = file_buffer.getvalue()
    manifest = {
        "hash": _sha256_bytes(payload),
        "metadata": {"source": "test"},
    }

    async def run():
        return await ingest_router.ingest_sip(
            file=UploadFile(file=BytesIO(payload), filename="ingest.png"),
            manifest=json.dumps(manifest),
            db=db_session,
        )

    response = asyncio.run(run())

    assert response["status"] == "success"
    assert response["fixity_check"] == "PASS"
    assert response["sha256"] == manifest["hash"]
    assert response["asset_id"] > 0

    asset = db_session.query(Asset).filter(Asset.id == response["asset_id"]).first()
    assert asset is not None
    assert asset.filename == "ingest.png"
    assert asset.status == "ready"
    assert asset.metadata_info["schema_version"] == "2.0"
    assert asset.metadata_info["technical"]["width"] == 8
    assert asset.metadata_info["technical"]["height"] == 8
    assert asset.metadata_info["technical"]["iiif_access_file_path"] == str(test_upload_dir / "ingest.png")
    assert asset.metadata_info["profile"]["key"] == "other"
    assert (test_upload_dir / "ingest.png").exists()
    assert queued == []


def test_ingest_sip_rejects_bad_fixity(monkeypatch, db_session, test_upload_dir):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))
    monkeypatch.setattr(ingest_router, "extract_metadata", lambda _path: {})

    file_buffer = _make_png_bytes()
    payload = file_buffer.getvalue()
    manifest = {
        "hash": "0" * 64,
        "metadata": {},
    }

    async def run():
        return await ingest_router.ingest_sip(
            file=UploadFile(file=BytesIO(payload), filename="broken.png"),
            manifest=json.dumps(manifest),
            db=db_session,
        )

    with pytest.raises(HTTPException) as exc_info:
      asyncio.run(run())

    assert exc_info.value.status_code == 400


def test_ingest_sip_queues_large_tiff_for_iiif_access_derivative(monkeypatch, db_session, test_upload_dir):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))
    monkeypatch.setattr(
        ingest_router,
        "extract_metadata",
        lambda _path: {"File": {"ImageWidth": 9000, "ImageHeight": 7000, "FileType": "TIFF"}},
    )
    queued: list[tuple[int, str]] = []
    monkeypatch.setattr(
        ingest_router.generate_iiif_access_derivative,
        "delay",
        lambda asset_id, file_path: queued.append((asset_id, file_path)),
    )

    payload = b"not-a-real-tiff-but-good-enough-for-policy"
    manifest = {
        "hash": _sha256_bytes(payload),
        "metadata": {},
    }

    async def run():
        return await ingest_router.ingest_sip(
            file=UploadFile(file=BytesIO(payload), filename="large.tif"),
            manifest=json.dumps(manifest),
            db=db_session,
        )

    response = asyncio.run(run())
    asset = db_session.query(Asset).filter(Asset.id == response["asset_id"]).first()

    assert asset is not None
    assert asset.status == "processing"
    assert asset.metadata_info["technical"]["derivative_rule_id"] == "tiff_large_pyramidal_tiled_copy"
    assert asset.metadata_info["technical"].get("iiif_access_file_path") in (None, "")
    assert queued == [(asset.id, str(test_upload_dir / "large.tif"))]


def test_ingest_sip_queues_psb_for_mandatory_iiif_access_derivative(monkeypatch, db_session, test_upload_dir):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))
    monkeypatch.setattr(
        ingest_router,
        "extract_metadata",
        lambda _path: {"File": {"ImageWidth": 1200, "ImageHeight": 900, "FileType": "PSB"}},
    )
    queued: list[tuple[int, str]] = []
    monkeypatch.setattr(
        ingest_router.generate_iiif_access_derivative,
        "delay",
        lambda asset_id, file_path: queued.append((asset_id, file_path)),
    )

    payload = b"fake-psb-data"
    manifest = {
        "hash": _sha256_bytes(payload),
        "metadata": {},
    }

    async def run():
        return await ingest_router.ingest_sip(
            file=UploadFile(file=BytesIO(payload), filename="master.psb"),
            manifest=json.dumps(manifest),
            db=db_session,
        )

    response = asyncio.run(run())
    asset = db_session.query(Asset).filter(Asset.id == response["asset_id"]).first()

    assert asset is not None
    assert asset.status == "processing"
    assert asset.metadata_info["technical"]["derivative_rule_id"] == "psb_mandatory_access_bigtiff"
    assert asset.metadata_info["technical"].get("iiif_access_file_path") in (None, "")
    assert queued == [(asset.id, str(test_upload_dir / "master.psb"))]
