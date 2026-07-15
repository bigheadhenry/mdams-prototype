from __future__ import annotations

from fastapi import HTTPException, status

from sqlalchemy.orm import Session

from ..models import Asset, ThreeDAsset, VideoAsset
from ..permissions import CurrentUser, can_access_visibility_scope, ensure_current_user


def _metadata_scope(metadata: object) -> str:
    if not isinstance(metadata, dict):
        return "open"
    core = metadata.get("core")
    if isinstance(core, dict) and isinstance(core.get("visibility_scope"), str):
        return str(core["visibility_scope"])
    return "open"


def assert_resource_visible(
    user: CurrentUser,
    *,
    visibility_scope: str | None,
    collection_object_id: int | None,
) -> None:
    current_user = ensure_current_user(user)
    if not can_access_visibility_scope(
        current_user,
        visibility_scope=visibility_scope or "open",
        collection_object_id=collection_object_id,
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Resource is outside the current user's visibility scope")


def assert_asset_visible(asset: Asset, user: CurrentUser) -> None:
    assert_resource_visible(
        user,
        visibility_scope=asset.visibility_scope or _metadata_scope(asset.metadata_info),
        collection_object_id=asset.collection_object_id,
    )


def assert_three_d_asset_visible(asset: ThreeDAsset, user: CurrentUser) -> None:
    assert_resource_visible(
        user,
        visibility_scope=_metadata_scope(asset.metadata_info),
        collection_object_id=asset.collection_object_id,
    )


def can_view_three_d_asset(asset: ThreeDAsset, user: CurrentUser) -> bool:
    try:
        assert_three_d_asset_visible(asset, user)
    except HTTPException:
        return False
    return True


PLATFORM_SOURCE_PERMISSIONS: dict[str, str] = {
    "image_2d": "image.view",
    "three_d": "three_d.view",
    "video": "video.view",
}


def can_access_platform_source(source_system: str, user: CurrentUser) -> bool:
    current_user = ensure_current_user(user)
    permission = PLATFORM_SOURCE_PERMISSIONS.get(source_system)
    return bool(permission and current_user.has_permission("platform.view") and current_user.has_permission(permission))


def _three_d_assets_for_source_id(source_id: str, db: Session) -> list[ThreeDAsset]:
    normalized_id = source_id.removeprefix("object-") if source_id.startswith("object-") else source_id
    if not normalized_id.isdigit():
        return []
    anchor = db.query(ThreeDAsset).filter(ThreeDAsset.id == int(normalized_id)).first()
    if anchor is None:
        return []
    if anchor.three_d_object_id is not None:
        return db.query(ThreeDAsset).filter(ThreeDAsset.three_d_object_id == anchor.three_d_object_id).all()
    query = db.query(ThreeDAsset).filter(ThreeDAsset.resource_group == anchor.resource_group)
    if anchor.collection_object_id is None:
        query = query.filter(ThreeDAsset.collection_object_id.is_(None))
    else:
        query = query.filter(ThreeDAsset.collection_object_id == anchor.collection_object_id)
    return query.all()


def assert_platform_resource_visible(
    source_system: str,
    source_id: str,
    db: Session,
    user: CurrentUser,
) -> None:
    current_user = ensure_current_user(user)
    if not current_user.has_permission("platform.view"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing permission: platform.view")
    permission = PLATFORM_SOURCE_PERMISSIONS.get(source_system)
    if permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource source not found")
    if not current_user.has_permission(permission):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Missing permission: {permission}")

    if source_system == "image_2d":
        if not source_id.isdigit():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
        asset = db.query(Asset).filter(Asset.id == int(source_id)).first()
        if asset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
        assert_asset_visible(asset, current_user)
        return

    if source_system == "three_d":
        assets = _three_d_assets_for_source_id(source_id, db)
        if not assets:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
        # A platform object aggregates multiple representations. Refuse the whole
        # aggregate if any representation is outside the caller's scope so its
        # title, files, preview or representation count cannot leak indirectly.
        for asset in assets:
            assert_three_d_asset_visible(asset, current_user)
        return

    if source_system == "video":
        if not source_id.isdigit() or db.query(VideoAsset.id).filter(VideoAsset.id == int(source_id)).first() is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")


def can_view_platform_resource(
    source_system: str,
    source_id: str,
    db: Session,
    user: CurrentUser,
) -> bool:
    try:
        assert_platform_resource_visible(source_system, source_id, db, user)
    except HTTPException:
        return False
    return True
