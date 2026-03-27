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
    monkeypatch.setattr(ingest_router.convert_psb_to_bigtiff, "delay", lambda *args, **kwargs: None)

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
    assert asset.metadata_info["profile"]["key"] == "other"
    assert (test_upload_dir / "ingest.png").exists()


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
