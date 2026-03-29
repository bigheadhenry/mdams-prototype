from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import User
from .services.auth import DEFAULT_USERS, get_user_by_session_token

PermissionName = str
RoleName = str


ROLE_PERMISSIONS: dict[RoleName, set[PermissionName]] = {
    "image_structured_editor": {"dashboard.view", "image.view", "image.edit", "platform.view"},
    "image_ingest_operator": {"dashboard.view", "image.view", "image.upload", "platform.view"},
    "image_ingest_reviewer": {"dashboard.view", "image.view", "image.ingest_review", "platform.view"},
    "image_resource_manager": {"dashboard.view", "image.view", "image.edit", "image.delete", "platform.view"},
    "three_d_operator": {"dashboard.view", "three_d.view", "three_d.upload", "three_d.edit", "platform.view"},
    "application_reviewer": {
        "dashboard.view",
        "image.view",
        "platform.view",
        "application.view_all",
        "application.review",
        "application.export",
    },
    "collection_owner": {
        "dashboard.view",
        "image.view",
        "image.edit_scope",
        "three_d.view",
        "three_d.edit_scope",
        "platform.view",
        "collection.scope",
    },
    "resource_user": {
        "dashboard.view",
        "image.view",
        "three_d.view",
        "platform.view",
        "application.create",
        "application.view_own",
    },
    "system_admin": {
        "dashboard.view",
        "image.view",
        "image.edit",
        "image.delete",
        "image.upload",
        "image.ingest_review",
        "three_d.view",
        "three_d.edit",
        "three_d.upload",
        "platform.view",
        "application.create",
        "application.view_all",
        "application.review",
        "application.export",
        "system.manage",
    },
}


DEMO_USER_PROFILE_MAP: dict[str, dict[str, object]] = {
    str(item["username"]).replace("_", "-"): item for item in DEFAULT_USERS
}


@dataclass
class CurrentUser:
    user_id: str
    display_name: str
    roles: set[RoleName]
    permissions: set[PermissionName]
    collection_scope: set[int]
    auth_mode: str = "session"

    def has_permission(self, permission: PermissionName) -> bool:
        return permission in self.permissions or "system.manage" in self.permissions


def _parse_collection_scope(raw_value: str | None) -> set[int]:
    if not raw_value:
        return set()
    scope: set[int] = set()
    for token in raw_value.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            scope.add(int(token))
        except ValueError:
            continue
    return scope


def _resolve_permissions(roles: set[RoleName]) -> set[PermissionName]:
    permissions: set[PermissionName] = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return permissions


def _build_current_user_from_db_user(user: User) -> CurrentUser:
    roles = {user_role.role.key for user_role in user.roles if user_role.role is not None}
    collection_scope = {
        int(item)
        for item in (user.collection_scope or [])
        if isinstance(item, int) or (isinstance(item, str) and item.isdigit())
    }
    return CurrentUser(
        user_id=user.username,
        display_name=user.display_name,
        roles=roles,
        permissions=_resolve_permissions(roles),
        collection_scope=collection_scope,
        auth_mode="session",
    )


def build_system_user() -> CurrentUser:
    roles = {"system_admin"}
    return CurrentUser(
        user_id="system_admin",
        display_name="System Admin",
        roles=roles,
        permissions=_resolve_permissions(roles),
        collection_scope=set(),
        auth_mode="fallback",
    )


def _build_legacy_demo_user(user_id: str, collection_scope: set[int]) -> CurrentUser:
    profile = DEMO_USER_PROFILE_MAP.get(user_id, DEMO_USER_PROFILE_MAP.get("system-admin", {}))
    roles = set(profile.get("roles", [])) or {"system_admin"}  # type: ignore[arg-type]
    return CurrentUser(
        user_id=str(profile.get("username") or user_id),
        display_name=str(profile.get("display_name") or user_id),
        roles=roles,
        permissions=_resolve_permissions(roles),
        collection_scope=collection_scope or set(profile.get("collection_scope", [])),  # type: ignore[arg-type]
        auth_mode="legacy-header",
    )


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_mdams_user: Annotated[str | None, Header(alias="X-MDAMS-User")] = None,
    x_mdams_collection_scope: Annotated[str | None, Header(alias="X-MDAMS-Collection-Scope")] = None,
) -> CurrentUser:
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            user = get_user_by_session_token(db, token.strip())
            if user is None:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session token")
            return _build_current_user_from_db_user(user)

    if x_mdams_user:
        legacy_scope = _parse_collection_scope(x_mdams_collection_scope)
        return _build_legacy_demo_user(x_mdams_user.strip().lower(), legacy_scope)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def ensure_current_user(value: object) -> CurrentUser:
    return value if isinstance(value, CurrentUser) else build_system_user()


def require_permission(permission: PermissionName):
    def dependency(user: CurrentUserDep) -> CurrentUser:
        if not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return user

    return dependency


def require_any_permission(*permissions: PermissionName):
    def dependency(user: CurrentUserDep) -> CurrentUser:
        if any(user.has_permission(permission) for permission in permissions):
            return user
        joined = ", ".join(permissions)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing one of permissions: {joined}",
        )

    return dependency


def can_access_visibility_scope(
    user: CurrentUser,
    *,
    visibility_scope: str | None,
    collection_object_id: int | None = None,
) -> bool:
    normalized_scope = (visibility_scope or "open").strip().lower()
    if normalized_scope == "open":
        return user.has_permission("image.view") or user.has_permission("three_d.view")
    if normalized_scope == "owner_only":
        if user.has_permission("system.manage"):
            return True
        if collection_object_id is None:
            return False
        return collection_object_id in user.collection_scope
    return False
