from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi import BackgroundTasks, HTTPException
from starlette.requests import Request

from app import config as app_config
from app.models import Asset
from app.permissions import build_system_user
from app.routers import downloads as downloads_router
from app.routers import iiif as iiif_router


pytestmark = [pytest.mark.unit, pytest.mark.contract]


class _FakeQuery:
    def __init__(self, asset: Asset | None):
        self._asset = asset

    def filter(self, *_args, **_kwargs):
        return self

    def first(self) -> Asset | None:
        return self._asset


class _FakeDB:
    def __init__(self, asset: Asset | None):
        self._asset = asset

    def query(self, _model):
        return _FakeQuery(self._asset)


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


def _build_asset(*, asset_id: int, original_path: Path, access_path: Path | None = None, fixity_sha256: str | None = None) -> Asset:
    technical = {
        "original_file_path": str(original_path),
        "original_file_name": original_path.name,
        "original_file_size": original_path.stat().st_size,
        "original_mime_type": "image/tiff",
        "width": 3200,
        "height": 2400,
    }
    if fixity_sha256:
        technical["fixity_sha256"] = fixity_sha256
    if access_path is not None:
        technical.update(
            {
                "iiif_access_file_path": str(access_path),
                "iiif_access_file_name": access_path.name,
                "iiif_access_mime_type": "image/tiff",
            }
        )

    return Asset(
        id=asset_id,
        filename=original_path.name,
        file_path=str(original_path),
        file_size=original_path.stat().st_size,
        mime_type="image/tiff",
        visibility_scope="open",
        collection_object_id=None,
        status="ready",
        resource_type="image_2d_cultural_object",
        process_message=None,
        created_at=datetime(2026, 4, 8, 9, 30, 0),
        metadata_info={
            "core": {
                "title": "North Hall Survey",
                "source_system": "image_2d",
                "source_id": str(asset_id),
                "visibility_scope": "open",
            },
            "management": {
                "project_name": "North Hall Project",
                "image_category": "documentation",
            },
            "technical": technical,
            "profile": {
                "key": "business_activity",
                "label": "业务活动",
                "sheet": "业务活动",
                "fields": {
                    "main_location": "North Hall",
                },
            },
            "raw_metadata": {},
        },
    )


def test_iiif_manifest_contract_uses_encoded_access_filename_and_layered_metadata(monkeypatch, tmp_path):
    monkeypatch.setattr(app_config, "API_PUBLIC_URL", "http://mdams.example/api")

    original_path = tmp_path / "master file.tif"
    access_path = tmp_path / "iiif access copy.tiff"
    original_path.write_bytes(b"original")
    access_path.write_bytes(b"access")

    asset = _build_asset(asset_id=5, original_path=original_path, access_path=access_path)

    manifest = iiif_router.get_iiif_manifest(
        asset_id=asset.id,
        request=_make_request({"host": "localhost:3000"}),
        db=_FakeDB(asset),
        user=build_system_user(),
    )

    body = manifest["items"][0]["items"][0]["items"][0]["body"]
    assert body["service"][0]["id"] == "http://mdams.example/api/iiif/5/service/iiif%20access%20copy.tiff"
    assert body["id"].endswith("/full/max/0/default.jpg")

    metadata_entries = {
        entry["label"]["en"][0]: entry["value"]["en"][0]
        for entry in manifest["metadata"]
    }
    assert metadata_entries["Shared Management Metadata / Project Name"] == "North Hall Project"
    assert metadata_entries["业务活动 / Main Location"] == "North Hall"


def test_download_bag_contract_includes_tag_files_and_stored_fixity(monkeypatch, tmp_path):
    original_path = tmp_path / "master.tif"
    access_path = tmp_path / "iiif-access copy.tiff"
    original_path.write_bytes(b"original")
    access_path.write_bytes(b"access")

    stored_fixity = "a" * 64
    asset = _build_asset(
        asset_id=9,
        original_path=original_path,
        access_path=access_path,
        fixity_sha256=stored_fixity,
    )

    monkeypatch.setattr(downloads_router, "_get_asset_or_404", lambda _asset_id, _db: asset)

    response = downloads_router.download_asset_bag(
        asset_id=asset.id,
        background_tasks=BackgroundTasks(),
        db=None,
    )

    with ZipFile(response.path) as zip_file:
        names = set(zip_file.namelist())
        bagit_text = zip_file.read(f"bag_{asset.id}/bagit.txt").decode("utf-8")
        bag_info_text = zip_file.read(f"bag_{asset.id}/bag-info.txt").decode("utf-8")
        manifest_text = zip_file.read(f"bag_{asset.id}/manifest-sha256.txt").decode("utf-8")

    assert f"bag_{asset.id}/data/{original_path.name}" in names
    assert f"bag_{asset.id}/data/{access_path.name}" in names
    assert bagit_text == "BagIt-Version: 1.0\nTag-File-Character-Encoding: UTF-8\n"
    assert f"{stored_fixity}  data/{original_path.name}" in manifest_text
    assert f"{hashlib.sha256(access_path.read_bytes()).hexdigest()}  data/{access_path.name}" in manifest_text
    assert f"Original-File: {original_path.name}" in bag_info_text
    assert f"IIIF-Access-File: {access_path.name}" in bag_info_text


def test_download_bag_returns_404_when_original_file_is_missing(monkeypatch, tmp_path):
    original_path = tmp_path / "missing-master.tif"
    asset = Asset(
        id=12,
        filename=original_path.name,
        file_path=str(original_path),
        file_size=0,
        mime_type="image/tiff",
        visibility_scope="open",
        collection_object_id=None,
        status="ready",
        resource_type="image_2d_cultural_object",
        process_message=None,
        metadata_info={
            "technical": {
                "original_file_path": str(original_path),
                "original_file_name": original_path.name,
            }
        },
    )

    monkeypatch.setattr(downloads_router, "_get_asset_or_404", lambda _asset_id, _db: asset)

    with pytest.raises(HTTPException) as exc_info:
        downloads_router.download_asset_bag(
            asset_id=asset.id,
            background_tasks=BackgroundTasks(),
            db=None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Physical file not found"
