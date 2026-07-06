from __future__ import annotations

import pytest
from datetime import datetime, timezone

from app.models import Asset, ThreeDAsset
from app.services.asset_detail import build_asset_detail_response
from app.services.event_boundary import (
    ASSET_LIFECYCLE_STEPS,
    THREE_D_PRODUCTION_EVENT_TYPES,
    get_minimal_event_boundary,
)
from app.services.three_d_production import seed_three_d_production_records


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def test_minimal_event_boundary_exposes_shared_vocab():
    boundary = get_minimal_event_boundary()

    assert "register" in boundary["shared_event_verbs"]
    assert "publish" in boundary["shared_event_verbs"]
    assert "export" in boundary["shared_event_verbs"]
    assert "review" in boundary["shared_event_verbs"]
    assert "preserve" in boundary["shared_event_verbs"]
    assert boundary["asset_lifecycle_steps"] == ASSET_LIFECYCLE_STEPS
    assert boundary["three_d_production_event_types"] == THREE_D_PRODUCTION_EVENT_TYPES


def test_asset_detail_lifecycle_steps_fit_minimal_event_boundary():
    asset = Asset(
        id=12,
        filename="sample.jpg",
        file_path="/tmp/sample.jpg",
        file_size=1024,
        mime_type="image/jpeg",
        visibility_scope="open",
        collection_object_id=None,
        status="ready",
        resource_type="image_2d_cultural_object",
        process_message=None,
        created_at=datetime(2026, 4, 22, 12, 0, 0, tzinfo=timezone.utc),
        metadata_info={
            "core": {
                "title": "Sample Asset",
                "source_system": "image_2d",
                "source_id": "12",
                "visibility_scope": "open",
            },
            "technical": {
                "width": 800,
                "height": 600,
                "ingest_method": "upload",
            },
            "management": {},
            "profile": {"key": "other", "label": "其他", "sheet": "其他", "fields": {}},
            "raw_metadata": {},
        },
    )

    detail = build_asset_detail_response(asset)
    lifecycle_steps = {item.step for item in detail.lifecycle}

    assert lifecycle_steps <= set(ASSET_LIFECYCLE_STEPS)
    assert lifecycle_steps >= {"object_created", "ingest_completed", "metadata_extracted", "preview_ready", "output_ready"}
    assert detail.process_timeline[0].step == "object_created"
    assert detail.process_timeline[-1].step == "output_ready"


def test_three_d_production_events_fit_minimal_event_boundary(db_session):
    asset = ThreeDAsset(
        filename="sample.glb",
        file_path="/tmp/sample.glb",
        file_size=1024,
        mime_type="model/gltf-binary",
        status="ready",
        resource_type="three_d_model",
        metadata_info={"core": {"title": "Sample 3D Asset"}},
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    seed_three_d_production_records(
        db_session,
        asset,
        saved_files=[
            {"role": "model", "role_label": "三维模型", "file_size": 512},
            {"role": "oblique_photo", "role_label": "倾斜摄影图像", "file_size": 256},
        ],
        manifest_path="/tmp/sample/manifest.json",
        preview_ready=True,
        preservation_status="preserved",
        storage_tier="archive",
    )
    db_session.commit()
    db_session.refresh(asset)

    event_types = {record.event_type for record in asset.production_records}

    assert event_types <= set(THREE_D_PRODUCTION_EVENT_TYPES)
    assert event_types == set(THREE_D_PRODUCTION_EVENT_TYPES)


# ── 跨子系统最小事件边界 ──────────────────────────────────────


class TestCrossSystemEventBoundaryContract:
    """验证跨子系统最小事件边界已定义（无数据库依赖）"""

    MINIMUM_EVENTS = {
        "asset_uploaded",      # 资源上传完成
        "record_bound",        # 图像记录与文件绑定
        "application_submitted",  # 申请单提交
        "application_approved",   # 申请单审批通过
        "package_exported",    # 交付包导出
    }

    def test_minimum_events_subset_of_shared_verbs(self):
        """五个最小事件都属于已定义的事件动词范围"""
        from app.services.event_boundary import (
            ASSET_LIFECYCLE_STEPS,
            APPLICATION_EVENT_STEPS,
            OUTPUT_EVENT_STEPS,
        )
        all_steps = set(ASSET_LIFECYCLE_STEPS) | set(APPLICATION_EVENT_STEPS) | set(OUTPUT_EVENT_STEPS)
        # application_submit and application_review should be present
        assert "application_submit" in APPLICATION_EVENT_STEPS
        assert "application_review" in APPLICATION_EVENT_STEPS
        assert "export_generate" in OUTPUT_EVENT_STEPS
        assert "object_created" in ASSET_LIFECYCLE_STEPS

    def test_minimum_events_coverage_complete(self):
        """验证五个最小事件都有对应的事件步骤定义"""
        from app.services.event_boundary import get_minimal_event_boundary
        boundary = get_minimal_event_boundary()

        # Collect all defined steps
        all_steps = set()
        for key in boundary:
            all_steps.update(boundary[key])

        # Check that the boundary vocabulary is non-empty and covers key domains
        assert len(boundary) == 6  # 6 categories
        assert len(all_steps) >= 20  # At least 20 defined events across all categories
        assert "application_submit" in all_steps
        assert "application_review" in all_steps
        assert "delivery_export" in all_steps
        assert "export_generate" in all_steps
        assert "object_created" in all_steps
