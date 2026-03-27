from __future__ import annotations

"""
Template for adding a new platform source adapter.

Copy this module when introducing a second source system. Implement the
three abstract methods and register the adapter in `app.platform.registry`.
"""

from sqlalchemy.orm import Session

from ..schemas import UnifiedResourceDetail, UnifiedResourceSourceSummary, UnifiedResourceSummary
from .base import PlatformSourceAdapter


class TemplateSourceAdapter(PlatformSourceAdapter):
    source_system = "template_source"
    source_label = "来源模板"
    resource_type = "template_resource"

    def list_source_summary(self, db: Session) -> UnifiedResourceSourceSummary:
        raise NotImplementedError("Replace this template with a concrete source adapter.")

    def list_unified_resources(
        self,
        db: Session,
        *,
        q: str | None = None,
        status: str | None = None,
        resource_type: str | None = None,
        profile_key: str | None = None,
        preview_enabled: bool | None = None,
    ) -> list[UnifiedResourceSummary]:
        raise NotImplementedError("Replace this template with a concrete source adapter.")

    def get_unified_resource(self, resource_id: str, db: Session) -> UnifiedResourceDetail:
        raise NotImplementedError("Replace this template with a concrete source adapter.")

