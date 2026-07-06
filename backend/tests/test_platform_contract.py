"""
三来源最小字段契约测试（无数据库依赖）

验证每个平台来源的 UnifiedResourceSummary / UnifiedResourceDetail 满足最小字段契约。
这些测试不依赖 PostgreSQL，可以在任何环境下运行。
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.platform.image_source import (
    SOURCE_SYSTEM as IMAGE_SOURCE_SYSTEM,
    Image2DSourceAdapter,
)
from app.platform.three_d_source import ThreeDSourceAdapter
from app.platform.video_source import (
    SOURCE_SYSTEM as VIDEO_SOURCE_SYSTEM,
    VideoSourceAdapter,
)
from app.schemas import (
    UnifiedResourceAction,
    UnifiedResourceDetail,
    UnifiedResourceSummary,
)

pytestmark = [pytest.mark.contract, pytest.mark.unit]

# ── Sources under test ──────────────────────────────────────

SOURCE_ADAPTERS: list[tuple[str, object]] = [
    ("image_2d", Image2DSourceAdapter()),
    ("three_d", ThreeDSourceAdapter()),
    ("video", VideoSourceAdapter()),
]


# ── Helper: build a minimal valid instance ──────────────────

def _make_minimal_summary(
    source_system: str = "test",
    source_id: str = "1",
    **overrides,
) -> UnifiedResourceSummary:
    """Construct a UnifiedResourceSummary with the minimum required fields."""
    data = {
        "id": f"{source_system}:{source_id}",
        "source_system": source_system,
        "source_id": source_id,
        "source_label": "测试来源",
        "title": "测试资源",
        "resource_type": "test_resource",
        "status": "ready",
        "preview_enabled": False,
        "manifest_url": f"/api/platform/resources/{source_system}/{source_id}",
        "detail_url": f"/api/platform/resources/{source_system}/{source_id}",
        "updated_at": "2026-07-06T00:00:00Z",
        "actions": [],
        **overrides,
    }
    return UnifiedResourceSummary(**data)


# ── Tests ──────────────────────────────────────────────────

class TestSummaryContract:
    """UnifiedResourceSummary 最小字段契约测试"""

    def test_required_fields_all_present(self):
        """验证必填字段不存在时抛出 ValidationError"""
        # 逐一移除必填字段
        required = [
            "id", "source_system", "source_id", "source_label",
            "title", "resource_type", "status", "preview_enabled",
            "manifest_url", "detail_url", "updated_at",
        ]
        for field in required:
            data = {
                "id": "test:1",
                "source_system": "test",
                "source_id": "1",
                "source_label": "测试",
                "title": "测试",
                "resource_type": "test",
                "status": "ready",
                "preview_enabled": False,
                "manifest_url": "/api/test/1",
                "detail_url": "/api/test/1",
                "updated_at": "2026-07-06T00:00:00Z",
                "actions": [],
            }
            del data[field]
            with pytest.raises(ValidationError, match=field):
                UnifiedResourceSummary(**data)

    def test_optional_fields_may_be_none(self):
        """验证 optional 字段可以为 None"""
        obj = UnifiedResourceSummary(
            id="test:1",
            source_system="test",
            source_id="1",
            source_label="测试",
            title="测试",
            resource_type="test",
            status="ready",
            preview_enabled=False,
            manifest_url="/api/test/1",
            detail_url="/api/test/1",
            updated_at="2026-07-06T00:00:00Z",
            actions=[],
            # All optional fields omitted
        )
        assert obj.profile_key is None
        assert obj.profile_label is None
        assert obj.thumbnail_url is None
        assert obj.preview_data is None
        assert obj.resolution is None
        assert obj.format is None
        assert obj.era is None
        assert obj.object_level is None
        assert obj.main_person is None
        assert obj.main_location is None

    def test_actions_structure(self):
        """验证 actions 中每个 action 的结构完整性"""
        action = UnifiedResourceAction(
            key="preview",
            label="预览",
            kind="preview",
            target="access_representation",
            url="/api/test/1/preview",
        )
        assert action.key == "preview"
        assert action.label == "预览"
        assert action.kind == "preview"
        assert action.target == "access_representation"
        assert action.url == "/api/test/1/preview"
        assert action.method == "GET"
        assert action.enabled is True

    def test_summary_with_full_actions(self):
        """验证完整 actions 列表可以被序列化"""
        actions = [
            UnifiedResourceAction(key="preview", label="预览", kind="preview", target="access"),
            UnifiedResourceAction(key="detail", label="详情", kind="detail", target="platform"),
        ]
        obj = _make_minimal_summary(actions=actions)
        assert len(obj.actions) == 2
        assert obj.actions[0].key == "preview"
        assert obj.actions[1].key == "detail"

    def test_source_system_in_id_format(self):
        """验证 id 格式为 {source_system}:{source_id}"""
        obj = _make_minimal_summary(source_system="image_2d", source_id="42")
        assert obj.id == "image_2d:42"


class TestDetailContract:
    """UnifiedResourceDetail 最小字段契约测试"""

    def test_detail_inherits_summary_fields(self):
        """验证 Detail 继承 Summary 的所有必填字段"""
        detail = UnifiedResourceDetail(
            id="test:1",
            source_system="test",
            source_id="1",
            source_label="测试",
            title="测试",
            resource_type="test",
            status="ready",
            preview_enabled=False,
            manifest_url="/api/test/1",
            detail_url="/api/test/1",
            updated_at="2026-07-06T00:00:00Z",
            actions=[],
            source_detail_url="/api/test/1/source",
        )
        assert detail.id == "test:1"
        assert detail.source_detail_url == "/api/test/1/source"
        assert detail.source_record_type is None
        assert detail.source_record_schema is None
        assert detail.source_record is None
        assert detail.rights_display is None

    def test_detail_requires_source_detail_url(self):
        """验证 source_detail_url 是必填的"""
        with pytest.raises(ValidationError, match="source_detail_url"):
            UnifiedResourceDetail(
                id="test:1",
                source_system="test",
                source_id="1",
                source_label="测试",
                title="测试",
                resource_type="test",
                status="ready",
                preview_enabled=False,
                manifest_url="/api/test/1",
                detail_url="/api/test/1",
                updated_at="2026-07-06T00:00:00Z",
                actions=[],
                # source_detail_url intentionally omitted
            )


class TestSourceAdapterContract:
    """来源适配器常量契约测试"""

    @pytest.mark.parametrize("system_name,adapter", SOURCE_ADAPTERS)
    def test_adapter_exposes_system_constants(self, system_name, adapter):
        """验证每个适配器暴露 source_system / source_label / resource_type"""
        assert hasattr(adapter, "source_system"), f"{system_name} missing source_system"
        assert hasattr(adapter, "source_label"), f"{system_name} missing source_label"
        assert hasattr(adapter, "resource_type"), f"{system_name} missing resource_type"
        assert isinstance(adapter.source_system, str)
        assert isinstance(adapter.source_label, str)
        assert isinstance(adapter.resource_type, str)

    @pytest.mark.parametrize("system_name,adapter", SOURCE_ADAPTERS)
    def test_adapter_source_system_unique(self, system_name, adapter):
        """验证 source_system 是三端唯一的"""
        systems = [name for name, _ in SOURCE_ADAPTERS]
        assert systems.count(adapter.source_system) == 1, \
            f"{adapter.source_system} is duplicated in SOURCE_ADAPTERS"

    @pytest.mark.parametrize("system_name,adapter", SOURCE_ADAPTERS)
    def test_adapter_has_required_methods(self, system_name, adapter):
        """验证适配器有 3 个核心方法签名"""
        assert hasattr(adapter, "list_source_summary")
        assert hasattr(adapter, "list_unified_resources")
        assert hasattr(adapter, "get_unified_resource_by_source")
        # 验证都是可调用的
        assert callable(adapter.list_source_summary)
        assert callable(adapter.list_unified_resources)
        assert callable(adapter.get_unified_resource_by_source)

    @pytest.mark.parametrize("system_name,adapter", SOURCE_ADAPTERS)
    def test_image_source_system_constant(self, system_name, adapter):
        """验证 image_2d 的 SOURCE_SYSTEM 与 Adapter 一致"""
        if system_name == "image_2d":
            assert adapter.source_system == IMAGE_SOURCE_SYSTEM
        if system_name == "video":
            assert adapter.source_system == VIDEO_SOURCE_SYSTEM
