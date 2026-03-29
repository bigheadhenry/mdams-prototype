import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.models import Asset
from app.permissions import build_system_user, get_current_user
from app.routers import assets as assets_router
from app.routers import iiif as iiif_router


pytestmark = [pytest.mark.unit, pytest.mark.integration]


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


def _create_asset(db_session, *, asset_id: int, filename: str, visibility_scope: str, collection_object_id: int | None):
    asset = Asset(
        id=asset_id,
        filename=filename,
        file_path=f"/tmp/{filename}",
        file_size=128,
        mime_type="image/jpeg",
        visibility_scope=visibility_scope,
        collection_object_id=collection_object_id,
        status="ready",
        resource_type="image_2d_cultural_object",
        metadata_info={
            "core": {
                "title": filename,
                "visibility_scope": visibility_scope,
                "collection_object_id": collection_object_id,
            },
            "technical": {},
            "management": {},
            "profile": {"key": "other", "label": "其他", "sheet": "其他", "fields": {}},
            "raw_metadata": {},
        },
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def test_asset_list_filters_owner_only_scope(db_session):
    open_asset = _create_asset(db_session, asset_id=1001, filename="open.jpg", visibility_scope="open", collection_object_id=None)
    owner_asset = _create_asset(db_session, asset_id=1002, filename="owner.jpg", visibility_scope="owner_only", collection_object_id=42)

    public_user = get_current_user(x_mdams_user="resource-user")
    owner_user = get_current_user(x_mdams_user="collection-owner", x_mdams_collection_scope="42")

    public_assets = assets_router.list_assets(db=db_session, user=public_user)
    owner_assets = assets_router.list_assets(db=db_session, user=owner_user)
    admin_assets = assets_router.list_assets(db=db_session, user=build_system_user())

    assert [asset.id for asset in public_assets] == [open_asset.id]
    assert {asset.id for asset in owner_assets} == {open_asset.id, owner_asset.id}
    assert {asset.id for asset in admin_assets} == {open_asset.id, owner_asset.id}


def test_iiif_manifest_blocks_hidden_assets(db_session):
    owner_asset = _create_asset(db_session, asset_id=2001, filename="hidden.jpg", visibility_scope="owner_only", collection_object_id=42)

    public_user = get_current_user(x_mdams_user="resource-user")
    owner_user = get_current_user(x_mdams_user="collection-owner", x_mdams_collection_scope="42")

    with pytest.raises(HTTPException) as exc:
        iiif_router.get_iiif_manifest(
            asset_id=owner_asset.id,
            request=_make_request({"host": "localhost:3000"}),
            db=db_session,
            user=public_user,
        )
    assert exc.value.status_code == 403

    manifest = iiif_router.get_iiif_manifest(
        asset_id=owner_asset.id,
        request=_make_request({"host": "localhost:3000"}),
        db=db_session,
        user=owner_user,
    )
    assert manifest["id"].endswith(f"/iiif/{owner_asset.id}/manifest")
    assert manifest["items"][0]["items"][0]["items"][0]["body"]["service"][0]["id"].endswith(
        f"/iiif/{owner_asset.id}/service/hidden.jpg"
    )
