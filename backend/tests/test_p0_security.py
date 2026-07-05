from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.permissions import ROLE_PERMISSIONS, CurrentUser
from app.routers import applications as applications_router
from app.routers import ingest as ingest_router
from app.routers import video as video_router
from app.schemas import ApplicationApproveRequest


REVIEWER = CurrentUser(
    user_id="application_reviewer",
    display_name="审批员",
    roles={"application_reviewer"},
    permissions={"application.review", "application.export"},
    collection_scope=set(),
)


def _route_permissions(router, path: str, method: str) -> set[str]:
    """Return permission names captured by require_permission dependencies."""
    permissions: set[str] = set()
    for route in router.routes:
        if getattr(route, "path", None) != path or method.upper() not in getattr(route, "methods", set()):
            continue
        for dependency in route.dependant.dependencies:
            call = dependency.call
            closure = getattr(call, "__closure__", None) or []
            for cell in closure:
                value = cell.cell_contents
                if isinstance(value, str):
                    permissions.add(value)
        return permissions
    raise AssertionError(f"Route not found: {method} {path}")


def test_ingest_sip_requires_image_upload_permission():
    assert "image.upload" in _route_permissions(ingest_router.router, "/ingest/sip", "POST")


@pytest.mark.parametrize(
    ("path", "method", "permission"),
    [
        ("/video/resources", "GET", "video.view"),
        ("/video/resources/{asset_id}", "GET", "video.view"),
        ("/video/resources/{asset_id}/stream", "GET", "video.view"),
        ("/video/resources/{asset_id}", "DELETE", "video.delete"),
    ],
)
def test_video_routes_require_explicit_permissions(path, method, permission):
    assert permission in _route_permissions(video_router.router, path, method)


def test_video_delete_permission_is_limited_to_manager_and_admin_roles():
    roles_with_delete = {
        role for role, permissions in ROLE_PERMISSIONS.items() if "video.delete" in permissions
    }
    assert roles_with_delete == {"image_resource_manager", "system_admin"}


@pytest.mark.parametrize("status", ["approved", "rejected", "fulfilled", "draft"])
def test_approve_only_accepts_submitted_applications(status):
    application = SimpleNamespace(status=status, id=1)
    with patch.object(applications_router, "_get_application_or_404", return_value=application):
        with pytest.raises(HTTPException) as exc_info:
            applications_router.approve_application(
                1,
                ApplicationApproveRequest(review_note="should fail"),
                db=MagicMock(),
                current_user=REVIEWER,
            )
    assert exc_info.value.status_code == 409


@pytest.mark.parametrize("status", ["approved", "rejected", "fulfilled", "draft"])
def test_reject_only_accepts_submitted_applications(status):
    application = SimpleNamespace(status=status, id=1)
    with patch.object(applications_router, "_get_application_or_404", return_value=application):
        with pytest.raises(HTTPException) as exc_info:
            applications_router.reject_application(
                1,
                ApplicationApproveRequest(review_note="should fail"),
                db=MagicMock(),
                current_user=REVIEWER,
            )
    assert exc_info.value.status_code == 409


@pytest.mark.parametrize("status", ["submitted", "rejected", "fulfilled", "draft"])
def test_export_only_accepts_approved_applications(status):
    application = SimpleNamespace(status=status, id=1)
    with patch.object(applications_router, "_get_application_or_404", return_value=application):
        with pytest.raises(HTTPException) as exc_info:
            applications_router.export_application(
                1,
                background_tasks=MagicMock(),
                db=MagicMock(),
                current_user=REVIEWER,
            )
    assert exc_info.value.status_code == 400
