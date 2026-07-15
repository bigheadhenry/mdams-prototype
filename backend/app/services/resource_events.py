from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..models import ResourceEvent, ThreeDProductionRecord
from ..permissions import CurrentUser


def record_resource_event(
    db: Session,
    *,
    source_system: str,
    source_id: str | int,
    event_type: str,
    status: str,
    actor: CurrentUser | None = None,
    description: str | None = None,
    evidence: str | None = None,
    metadata: dict[str, Any] | None = None,
    three_d_asset_id: int | None = None,
) -> ResourceEvent:
    event = ResourceEvent(
        source_system=source_system,
        source_id=str(source_id),
        event_type=event_type,
        status=status,
        actor_user_id=actor.user_id if actor else None,
        actor_display_name=actor.display_name if actor else None,
        description=description,
        evidence=evidence,
        metadata_info=metadata or {},
    )
    db.add(event)
    if three_d_asset_id is not None:
        db.add(
            ThreeDProductionRecord(
                asset_id=three_d_asset_id,
                stage=event_type,
                event_type=event_type,
                status=status,
                actor=actor.display_name if actor else None,
                description=description,
                evidence=evidence,
                metadata_info=metadata or {},
            )
        )
    return event
