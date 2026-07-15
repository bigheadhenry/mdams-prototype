from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Asset, ThreeDAsset, ThreeDCollectionObject, ThreeDDigitalObject
from app.permissions import CurrentUser, get_current_user
from app.routers import platform as platform_router
from app.services.search_engine import SearchResponse, SearchResult
from app.services.search_engine import engine as search_engine_module


pytestmark = [pytest.mark.unit]


@pytest.fixture()
def policy_db():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def _user(name: str, *, scope: set[int] | None = None, permissions: set[str] | None = None) -> CurrentUser:
    return CurrentUser(
        user_id=name,
        display_name=name,
        roles={"test"},
        permissions=permissions or {"platform.view", "image.view", "three_d.view", "video.view"},
        collection_scope=scope or set(),
    )


def _asset(db, name: str, visibility: str, collection_id: int | None) -> Asset:
    item = Asset(
        filename=name,
        file_path=f"/missing/{name}",
        file_size=1,
        mime_type="image/jpeg",
        visibility_scope=visibility,
        collection_object_id=collection_id,
        status="ready",
        resource_type="image_2d_cultural_object",
        metadata_info={
            "core": {"title": name, "visibility_scope": visibility},
            "technical": {},
            "management": {},
            "profile": {"key": "other", "label": "其他", "fields": {}},
            "raw_metadata": {},
        },
    )
    db.add(item)
    db.flush()
    return item


def _three_d_asset(db, name: str, visibility: str, collection_id: int) -> ThreeDAsset:
    collection = ThreeDCollectionObject(
        id=collection_id,
        object_number=f"OBJ-{collection_id}",
        object_name=name,
    )
    digital_object = ThreeDDigitalObject(
        object_key=f"object-{collection_id}",
        collection_object=collection,
        title=name,
        lifecycle_status="draft",
        metadata_info={},
    )
    item = ThreeDAsset(
        three_d_object=digital_object,
        collection_object=collection,
        resource_group=f"group-{collection_id}",
        filename=f"{name}.glb",
        file_path=f"/missing/{name}.glb",
        file_size=1,
        mime_type="model/gltf-binary",
        resource_type="three_d_model",
        status="ready",
        representation_type="web_display",
        publication_status="draft",
        metadata_info={
            "core": {"title": name, "visibility_scope": visibility, "profile_key": "other"},
            "technical": {},
            "management": {},
            "profile": {"fields": {}},
            "raw_metadata": {},
        },
    )
    db.add(item)
    db.flush()
    return item


def _seed_resources(db):
    open_image = _asset(db, "open-image.jpg", "open", None)
    hidden_image = _asset(db, "hidden-image.jpg", "owner_only", 42)
    second_open_image = _asset(db, "second-open.jpg", "open", None)
    open_model = _three_d_asset(db, "open-model", "open", 41)
    hidden_model = _three_d_asset(db, "hidden-model", "owner_only", 42)
    db.commit()
    return open_image, hidden_image, second_open_image, open_model, hidden_model


def test_platform_adapter_fallback_filters_lists_counts_and_details(policy_db, monkeypatch):
    open_image, hidden_image, second_open_image, open_model, hidden_model = _seed_resources(policy_db)
    monkeypatch.setattr(platform_router, "get_engine", lambda: None)
    public = _user("public")
    owner = _user("owner", scope={42})

    public_page = platform_router.get_resources(db=policy_db, user=public)
    public_ids = {item.id for item in public_page.items}
    assert f"image_2d:{open_image.id}" in public_ids
    assert f"image_2d:{second_open_image.id}" in public_ids
    assert f"three_d:object-{open_model.id}" in public_ids
    assert f"image_2d:{hidden_image.id}" not in public_ids
    assert f"three_d:object-{hidden_model.id}" not in public_ids
    assert public_page.total == 3

    owner_page = platform_router.get_resources(db=policy_db, user=owner)
    assert owner_page.total == 5

    public_sources = {item.source_system: item.resource_count for item in platform_router.get_sources(db=policy_db, user=public)}
    assert public_sources == {"image_2d": 2, "three_d": 1, "video": 0}

    with pytest.raises(HTTPException) as hidden_detail:
        platform_router.get_resource_by_source(
            source_system="image_2d",
            source_id=str(hidden_image.id),
            db=policy_db,
            user=public,
        )
    assert hidden_detail.value.status_code == 403

    with pytest.raises(HTTPException) as legacy_hidden_detail:
        platform_router.get_resource(
            resource_id=f"three_d:object-{hidden_model.id}",
            db=policy_db,
            user=public,
        )
    assert legacy_hidden_detail.value.status_code == 403
    assert platform_router.get_resource_by_source(
        source_system="three_d",
        source_id=f"object-{hidden_model.id}",
        db=policy_db,
        user=owner,
    ).source_id == f"object-{hidden_model.id}"


class _IndexedDocuments:
    def __init__(self, documents: list[dict]):
        self.documents = documents

    def health(self) -> bool:
        return True

    def search(self, query) -> SearchResponse:
        selected = self.documents[query.skip : query.skip + query.limit]
        return SearchResponse(
            items=[SearchResult(id=str(item["id"]), document=item) for item in selected],
            total=len(self.documents),
        )


def _document(asset_id: int, title: str) -> dict:
    return {
        "id": f"image_2d:{asset_id}",
        "source_system": "image_2d",
        "source_id": str(asset_id),
        "source_label": "二维影像子系统",
        "title": title,
        "resource_type": "image_2d_cultural_object",
        "status": "ready",
        "preview_enabled": True,
        "manifest_url": f"/api/iiif/{asset_id}/manifest",
        "detail_url": f"/api/platform/resources/image_2d/{asset_id}",
        "thumbnail_url": f"/api/assets/{asset_id}/preview",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def test_meilisearch_path_rechecks_stale_documents_and_paginates_after_policy(policy_db, monkeypatch):
    open_image, hidden_image, second_open_image, _, _ = _seed_resources(policy_db)
    stale_id = 999999
    engine = _IndexedDocuments([
        _document(hidden_image.id, "private title must not leak"),
        _document(stale_id, "deleted private title must not leak"),
        _document(open_image.id, "visible one"),
        _document(second_open_image.id, "visible two"),
    ])
    monkeypatch.setattr(platform_router, "get_engine", lambda: engine)
    monkeypatch.setattr(search_engine_module, "get_engine", lambda: engine)

    page = platform_router.get_resources(skip=1, limit=1, db=policy_db, user=_user("public"))
    assert page.total == 2
    assert [item.source_id for item in page.items] == [str(second_open_image.id)]
    serialized = page.model_dump_json()
    assert "private title" not in serialized
    assert str(stale_id) not in serialized

    related = platform_router.get_related_resources(
        object_number="DRILL-OBJ",
        exclude_source=None,
        exclude_id=None,
        skip=0,
        limit=20,
        db=policy_db,
        user=_user("public"),
    )
    assert related.total == 2
    assert {item.source_id for item in related.items} == {str(open_image.id), str(second_open_image.id)}


def test_platform_authentication_and_source_permission_are_required(policy_db, monkeypatch):
    open_image, *_ = _seed_resources(policy_db)
    monkeypatch.setattr(platform_router, "get_engine", lambda: None)

    with pytest.raises(HTTPException) as anonymous:
        get_current_user(db=policy_db)
    assert anonymous.value.status_code == 401

    no_platform = _user("no-platform", permissions={"image.view"})
    with pytest.raises(HTTPException) as forbidden:
        platform_router.get_resource_by_source(
            source_system="image_2d",
            source_id=str(open_image.id),
            db=policy_db,
            user=no_platform,
        )
    assert forbidden.value.status_code == 403

    image_only = _user("image-only", permissions={"platform.view", "image.view"})
    page = platform_router.get_resources(db=policy_db, user=image_only)
    assert page.total == 2
    assert {item.source_system for item in page.items} == {"image_2d"}
    assert {item.source_system for item in platform_router.get_sources(db=policy_db, user=image_only)} == {"image_2d"}
