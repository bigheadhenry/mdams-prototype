from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request

from app import config as app_config
from app.models import Asset
from app.permissions import build_system_user
from app.routers import downloads as downloads_router
from app.routers import iiif as iiif_router
from app.tasks import generate_iiif_access_derivative


pytestmark = [pytest.mark.integration, pytest.mark.contract]


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


def _create_asset(db_session, *, asset_id: int, original_path: Path, access_path: Path | None = None, status: str = "ready") -> Asset:
    technical = {
        "original_file_path": str(original_path),
        "original_file_name": original_path.name,
        "original_file_size": original_path.stat().st_size,
        "original_mime_type": "image/tiff" if original_path.suffix.lower() in {".tif", ".tiff"} else "application/octet-stream",
        "width": 9000,
        "height": 7000,
        "derivative_rule_id": "tiff_large_pyramidal_tiled_copy",
        "derivative_strategy": "generate_pyramidal_tiff",
        "derivative_priority": "required",
        "derivative_source_family": "tiff",
    }
    if access_path is not None:
        technical.update(
            {
                "iiif_access_file_path": str(access_path),
                "iiif_access_file_name": access_path.name,
                "iiif_access_mime_type": "image/tiff",
                "conversion_method": "test_conversion",
            }
        )

    asset = Asset(
        id=asset_id,
        filename=original_path.name,
        file_path=str(original_path),
        file_size=original_path.stat().st_size,
        mime_type=technical["original_mime_type"],
        visibility_scope="open",
        collection_object_id=None,
        status=status,
        resource_type="image_2d_cultural_object",
        process_message=None,
        metadata_info={
            "core": {
                "title": original_path.name,
                "source_system": "image_2d",
                "source_id": str(asset_id),
                "visibility_scope": "open",
            },
            "technical": technical,
            "management": {},
            "profile": {"key": "other", "label": "Other", "sheet": "Other", "fields": {}},
            "raw_metadata": {},
        },
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def test_manifest_and_download_prefer_iiif_access_copy(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr(app_config, "CANTALOUPE_PUBLIC_URL", "http://cantaloupe:8182/iiif/2")
    monkeypatch.setattr(app_config, "API_PUBLIC_URL", "http://localhost:3000/api")

    original_path = tmp_path / "master.tif"
    access_path = tmp_path / "derivatives" / "asset-1" / "iiif-access.pyramidal.tiff"
    access_path.parent.mkdir(parents=True, exist_ok=True)
    original_path.write_bytes(b"original")
    access_path.write_bytes(b"access-copy")

    asset = _create_asset(db_session, asset_id=1, original_path=original_path, access_path=access_path)

    manifest = iiif_router.get_iiif_manifest(
        asset_id=asset.id,
        request=_make_request({"host": "localhost:3000"}),
        db=db_session,
        user=build_system_user(),
    )
    service_id = manifest["items"][0]["items"][0]["items"][0]["body"]["service"][0]["id"]
    assert service_id == (
        "http://localhost:3000/api/iiif/1/service/"
        "derivatives/asset-1/iiif-access.pyramidal.tiff"
    )

    download_response = downloads_router.download_asset_file(asset_id=asset.id, db=db_session)
    assert Path(download_response.path) == access_path

    bag_response = downloads_router.download_asset_bag(
        asset_id=asset.id,
        background_tasks=BackgroundTasks(),
        db=db_session,
    )
    with ZipFile(bag_response.path) as zip_file:
        names = set(zip_file.namelist())
    assert f"bag_{asset.id}/data/{original_path.name}" in names
    assert f"bag_{asset.id}/data/{access_path.name}" in names


def test_manifest_returns_409_when_required_access_copy_not_ready(db_session, tmp_path, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(tmp_path))

    original_path = tmp_path / "master.psb"
    original_path.write_bytes(b"psb")
    asset = _create_asset(db_session, asset_id=2, original_path=original_path, access_path=None, status="processing")
    asset.metadata_info["technical"]["derivative_rule_id"] = "psb_mandatory_access_bigtiff"
    asset.metadata_info["technical"]["derivative_source_family"] = "psb"
    db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        iiif_router.get_iiif_manifest(
            asset_id=asset.id,
            request=_make_request({"host": "localhost:3000"}),
            db=db_session,
            user=build_system_user(),
        )

    assert exc_info.value.status_code == 409


def test_background_task_keeps_original_and_records_access_copy(monkeypatch, db_session, tmp_path):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(tmp_path))
    monkeypatch.setattr("app.tasks.SessionLocal", sessionmaker(bind=db_session.get_bind(), autocommit=False, autoflush=False))

    original_path = tmp_path / "master.psb"
    original_path.write_bytes(b"psb")
    asset = _create_asset(db_session, asset_id=3, original_path=original_path, access_path=None, status="processing")
    asset.metadata_info["technical"]["derivative_rule_id"] = "psb_mandatory_access_bigtiff"
    asset.metadata_info["technical"]["derivative_source_family"] = "psb"
    db_session.commit()

    def _fake_generate(source_path: str, output_path: str):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"iiif-access")
        return 1200, 900

    monkeypatch.setattr("app.tasks.generate_pyramidal_tiff_access_copy", _fake_generate)

    generate_iiif_access_derivative.run(asset.id, str(original_path))
    db_session.refresh(asset)

    assert asset.file_path == str(original_path)
    assert asset.status == "ready"
    assert asset.metadata_info["technical"]["iiif_access_file_path"].endswith("iiif-access.pyramidal.tiff")
    assert asset.metadata_info["technical"]["original_file_path"] == str(original_path)
    assert asset.metadata_info["technical"]["iiif_access_file_path"] != str(original_path)
