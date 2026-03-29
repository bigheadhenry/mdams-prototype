import pytest
from fastapi import HTTPException

from app.permissions import (
    can_access_visibility_scope,
    get_current_user,
    require_permission,
)


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def test_auth_context_resolves_demo_user():
    user = get_current_user(x_mdams_user="resource-user")

    assert user.user_id == "resource_user"
    assert "resource_user" in user.roles
    assert user.has_permission("application.create") is True
    assert user.has_permission("application.review") is False


def test_resource_user_cannot_use_review_permission():
    user = get_current_user(x_mdams_user="resource-user")
    dependency = require_permission("application.review")

    with pytest.raises(HTTPException) as exc:
        dependency(user)

    assert exc.value.status_code == 403


def test_collection_owner_can_access_own_scope_only():
    owner = get_current_user(
        x_mdams_user="collection-owner",
        x_mdams_collection_scope="1,7",
    )

    assert can_access_visibility_scope(owner, visibility_scope="open") is True
    assert can_access_visibility_scope(owner, visibility_scope="owner_only") is False
    assert can_access_visibility_scope(owner, visibility_scope="owner_only", collection_object_id=1) is True
    assert can_access_visibility_scope(owner, visibility_scope="owner_only", collection_object_id=99) is False
