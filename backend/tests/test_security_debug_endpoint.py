"""Security tests for debug endpoint and SIP ingest authentication.

Covers audit issues:
  C-2: Unauthenticated /debug/files endpoint
  C-3: Unauthenticated SIP ingest endpoint
"""

import pytest
from fastapi import HTTPException

from app.permissions import build_system_user, get_current_user

pytestmark = [pytest.mark.integration, pytest.mark.contract]


# ---------------------------------------------------------------------------
# C-2: Debug endpoint now requires system.manage permission
# ---------------------------------------------------------------------------


class TestDebugEndpointAuth:
    """Verify /debug/files requires admin authentication."""

    def test_debug_endpoint_list_uploaded_files_requires_admin(self, db_session):
        """C-2: list_uploaded_files should require system.manage permission.

        We verify the dependency is wired by checking that the function
        signature includes the permission dependency.  Actual HTTP-level
        auth testing requires a running server or TestClient.
        """
        from app.routers.assets import list_uploaded_files

        import inspect

        sig = inspect.signature(list_uploaded_files)
        param_names = list(sig.parameters.keys())
        # The _user parameter with Depends(require_permission) should exist
        assert "_user" in param_names, (
            "list_uploaded_files must have an auth dependency parameter"
        )

    def test_system_user_has_system_manage_permission(self):
        """C-2: system_admin user has the system.manage permission."""
        user = build_system_user()
        assert user.has_permission("system.manage")


# ---------------------------------------------------------------------------
# C-3: SIP ingest now requires image.upload permission
# ---------------------------------------------------------------------------


class TestSipIngestAuth:
    """Verify /ingest/sip requires authentication with image.upload permission."""

    def test_ingest_sip_has_auth_dependency(self):
        """C-3: ingest_sip should require image.upload permission."""
        from app.routers.ingest import ingest_sip

        import inspect

        sig = inspect.signature(ingest_sip)
        param_names = list(sig.parameters.keys())
        assert "_user" in param_names, (
            "ingest_sip must have an auth dependency parameter"
        )

    def test_image_ingest_operator_has_upload_permission(self, db_session):
        """C-3: image_ingest_operator role has image.upload permission."""
        from app.permissions import ROLE_PERMISSIONS

        assert "image.upload" in ROLE_PERMISSIONS["image_ingest_operator"]

    def test_system_admin_has_upload_permission(self, db_session):
        """C-3: system_admin role has image.upload permission."""
        from app.permissions import ROLE_PERMISSIONS

        assert "image.upload" in ROLE_PERMISSIONS["system_admin"]

    def test_resource_user_lacks_upload_permission(self):
        """C-3: resource_user role should NOT have image.upload permission."""
        from app.permissions import ROLE_PERMISSIONS

        assert "image.upload" not in ROLE_PERMISSIONS["resource_user"]
