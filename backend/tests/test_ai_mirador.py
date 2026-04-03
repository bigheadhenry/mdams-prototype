import asyncio

import pytest
from starlette.requests import Request

from app.models import Asset
from app.permissions import build_system_user, get_current_user
from app.routers import ai_mirador


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


def _create_asset(
    db_session,
    *,
    asset_id: int,
    title: str,
    visibility_scope: str = "open",
    collection_object_id: int | None = None,
):
    asset = Asset(
        id=asset_id,
        filename=f"{title.replace(' ', '_').lower()}.jpg",
        file_path=f"/tmp/{title.replace(' ', '_').lower()}.jpg",
        file_size=128,
        mime_type="image/jpeg",
        visibility_scope=visibility_scope,
        collection_object_id=collection_object_id,
        status="ready",
        resource_type="image_2d_cultural_object",
        metadata_info={
            "core": {
                "title": title,
                "object_number": title,
                "visibility_scope": visibility_scope,
                "collection_object_id": collection_object_id,
                "resource_id": f"image_2d:{asset_id}",
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


async def _interpret(payload, request, db_session, user):
    return await ai_mirador.interpret_mirador_command(
        payload=payload,
        request=request,
        db=db_session,
        user=user,
    )


def test_interpret_mirador_command_uses_openai_compare_search_and_excludes_current_asset(db_session, monkeypatch):
    current_asset = _create_asset(db_session, asset_id=101, title="Blue Vase")
    target_asset = _create_asset(db_session, asset_id=102, title="Blue Vase Study")
    _create_asset(db_session, asset_id=103, title="Hidden Vase", visibility_scope="owner_only", collection_object_id=42)

    async def _openai_plan(payload):
        return {
            "action": "open_compare",
            "assistant_message": "I found a matching image.",
            "requires_confirmation": True,
            "search_query": "blue vase",
            "compare_mode": "side_by_side",
        }

    monkeypatch.setattr(ai_mirador, "_call_openai_plan", _openai_plan)

    plan = asyncio.run(
        _interpret(
            ai_mirador.MiradorAIRequest(
                prompt="please compare blue vase",
                current_asset_id=current_asset.id,
                current_manifest_url="http://localhost:3000/api/iiif/101/manifest",
                current_title=current_asset.filename,
                current_object_number="Blue Vase",
                current_resource_id="image_2d:101",
                max_candidates=5,
            ),
            _make_request({"host": "localhost:3000"}),
            db_session,
            build_system_user(),
        )
    )

    assert plan.action == "open_compare"
    assert plan.requires_confirmation is True
    assert plan.search_query == "blue vase"
    assert plan.search_results
    assert plan.target_asset is not None
    assert plan.target_asset.asset_id == target_asset.id
    assert all(result.asset_id != current_asset.id for result in plan.search_results)


def test_interpret_mirador_command_falls_back_to_search_when_compare_has_no_candidates(db_session, monkeypatch):
    _create_asset(db_session, asset_id=201, title="Unrelated Archive")

    async def _openai_plan(payload):
        return {
            "action": "open_compare",
            "assistant_message": "I could not find a clear match.",
            "requires_confirmation": True,
            "search_query": "missing artifact",
            "compare_mode": "side_by_side",
        }

    monkeypatch.setattr(ai_mirador, "_call_openai_plan", _openai_plan)

    plan = asyncio.run(
        _interpret(
            ai_mirador.MiradorAIRequest(
                prompt="please compare missing artifact",
                current_asset_id=201,
                current_manifest_url="http://localhost:3000/api/iiif/201/manifest",
                current_title="Unrelated Archive",
                current_object_number="201",
                current_resource_id="image_2d:201",
                max_candidates=5,
            ),
            _make_request({"host": "localhost:3000"}),
            db_session,
            build_system_user(),
        )
    )

    assert plan.action == "search_assets"
    assert plan.requires_confirmation is False
    assert plan.search_results == []
    assert plan.assistant_message


def test_search_assets_endpoint_honors_visibility_scope(db_session):
    open_asset = _create_asset(db_session, asset_id=301, title="Blue Lamp")
    hidden_asset = _create_asset(
        db_session,
        asset_id=302,
        title="Blue Lamp Archive",
        visibility_scope="owner_only",
        collection_object_id=42,
    )

    public_user = get_current_user(x_mdams_user="resource-user")
    owner_user = get_current_user(x_mdams_user="collection-owner", x_mdams_collection_scope="42")

    public_results = ai_mirador.search_assets(
        q="blue lamp",
        request=_make_request({"host": "localhost:3000"}),
        limit=10,
        db=db_session,
        user=public_user,
    )
    owner_results = ai_mirador.search_assets(
        q="blue lamp",
        request=_make_request({"host": "localhost:3000"}),
        limit=10,
        db=db_session,
        user=owner_user,
    )
    admin_results = ai_mirador.search_assets(
        q="blue lamp",
        request=_make_request({"host": "localhost:3000"}),
        limit=10,
        db=db_session,
        user=build_system_user(),
    )

    assert [result.asset_id for result in public_results] == [open_asset.id]
    assert {result.asset_id for result in owner_results} == {open_asset.id, hidden_asset.id}
    assert {result.asset_id for result in admin_results} == {open_asset.id, hidden_asset.id}
    assert public_results[0].manifest_url.endswith(f"/iiif/{open_asset.id}/manifest")
