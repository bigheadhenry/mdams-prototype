from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from ..schemas import (
    UnifiedResourceDetail,
    UnifiedResourceSourceSummary,
    UnifiedResourceSummary,
)


class PlatformSourceAdapter(ABC):
    """Base contract for a platform source adapter."""

    source_system: str
    source_label: str
    resource_type: str

    @abstractmethod
    def list_source_summary(self, db: Session) -> UnifiedResourceSourceSummary:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    def get_unified_resource_by_source(
        self,
        source_system: str,
        source_id: str,
        db: Session,
    ) -> UnifiedResourceDetail:
        raise NotImplementedError

    def get_unified_resource(self, resource_id: str, db: Session) -> UnifiedResourceDetail:
        source_system, separator, source_id = resource_id.partition(":")
        if not separator:
            raise ValueError("Unknown unified resource id")
        return self.get_unified_resource_by_source(source_system, source_id, db)
