from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from sqlalchemy.orm import Session

from ..models import ThreeDAsset, ThreeDProductionRecord


def record_three_d_event(
    db: Session,
    asset: ThreeDAsset,
    *,
    stage: str,
    event_type: str,
    status: str,
    description: str | None = None,
    actor: str | None = None,
    evidence: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ThreeDProductionRecord:
    record = ThreeDProductionRecord(
        asset_id=asset.id,
        stage=stage,
        event_type=event_type,
        status=status,
        actor=actor,
        description=description,
        evidence=evidence,
        metadata_info=dict(metadata or {}),
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.flush()
    return record


def seed_three_d_production_records(
    db: Session,
    asset: ThreeDAsset,
    *,
    saved_files: Sequence[Mapping[str, Any]],
    manifest_path: str,
    preview_ready: bool,
    preservation_status: str,
    storage_tier: str,
) -> None:
    record_three_d_event(
        db,
        asset,
        stage='ingest',
        event_type='register',
        status='success',
        description='三维资源完成入库登记',
        metadata={'file_count': len(saved_files)},
    )
    record_three_d_event(
        db,
        asset,
        stage='processing',
        event_type='files_saved',
        status='success',
        description='三维资源文件已按角色保存',
        metadata={'roles': [str(record.get('role') or 'other') for record in saved_files]},
    )
    record_three_d_event(
        db,
        asset,
        stage='processing',
        event_type='manifest_built',
        status='success',
        description='三维资源清单已生成',
        evidence=manifest_path,
        metadata={'manifest_path': manifest_path},
    )
    record_three_d_event(
        db,
        asset,
        stage='publish',
        event_type='web_preview',
        status='success' if preview_ready else 'pending',
        description='Web 展示状态已登记',
        metadata={'web_preview_status': asset.web_preview_status},
    )
    record_three_d_event(
        db,
        asset,
        stage='preservation',
        event_type='storage_tier',
        status='success' if preservation_status == 'preserved' else 'pending',
        description='保存层状态已登记',
        metadata={'storage_tier': storage_tier, 'preservation_status': preservation_status},
    )
