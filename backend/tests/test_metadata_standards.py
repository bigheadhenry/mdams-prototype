"""Tests for Dublin Core 15 metadata standards mapping."""

import pytest
from datetime import datetime

from app.services.metadata_standards import (
    to_dublin_core,
    to_dublin_core_json,
    from_unified_resource_detail,
)


class TestToDublinCore:
    def test_minimal_output(self):
        """Only the fixed defaults (publisher, language) appear."""
        result = to_dublin_core(title="测试资源")
        assert result.get("dc:title") == "测试资源"
        assert result.get("dc:publisher") == "故宫博物院"
        assert result.get("dc:language") == "zh-CN"
        assert len(result) == 3  # title + publisher + language

    def test_all_fields_populated(self):
        result = to_dublin_core(
            title="清乾隆 各色釉彩大瓶",
            creator="李摄影师",
            subject="各色釉彩大瓶 · 清 · 正面拍摄",
            description="乾隆时期大型瓷器正面拍摄影像",
            publisher="故宫博物院",
            contributor="王助理",
            date="2026-06-01",
            type_="image_2d_cultural_object",
            format_="TIFF / 6000x4000",
            identifier="image_2d:42",
            language="zh-CN",
            rights="故宫所有；仅限学术用途",
        )
        assert result["dc:title"] == "清乾隆 各色釉彩大瓶"
        assert result["dc:creator"] == "李摄影师"
        assert result["dc:identifier"] == "image_2d:42"
        assert len(result) == 12

    def test_empty_values_omitted(self):
        """None or empty values should not appear in output."""
        result = to_dublin_core(title="Test", creator="", subject=None)
        assert "dc:subject" not in result
        assert "dc:creator" not in result
        assert "dc:title" in result

    def test_source_relation_coverage_never_output(self):
        """These three elements are intentionally never mapped."""
        result = to_dublin_core(title="Test")
        assert "dc:source" not in result
        assert "dc:relation" not in result
        assert "dc:coverage" not in result

    def test_rights_from_copyright_and_restrictions(self):
        result = to_dublin_core(
            title="Test",
            rights="故宫所有；禁止商业用途",
        )
        assert result.get("dc:rights") == "故宫所有；禁止商业用途"


class TestToDublinCoreJson:
    def test_wraps_in_dublin_core_key(self):
        result = to_dublin_core_json(title="Test")
        assert "dublin_core" in result
        assert result["dublin_core"]["dc:title"] == "Test"

    def test_clean_json_structure(self):
        result = to_dublin_core_json(title="A", date="2026-01-01")
        dc = result["dublin_core"]
        assert set(dc.keys()) == {"dc:title", "dc:publisher", "dc:language", "dc:date"}


class TestFromUnifiedResourceDetail:
    def test_from_minimal_detail(self):
        """A bare-minimum resource detail."""
        detail = _make_detail(
            title="Test Image",
            source_system="image_2d",
            source_id="1",
            resource_type="image",
            updated_at=datetime(2026, 6, 1),
        )
        result = from_unified_resource_detail(detail)
        dc = result["dublin_core"]
        assert dc["dc:title"] == "Test Image"
        assert dc["dc:identifier"] == "image_2d:1"
        assert dc["dc:publisher"] == "故宫博物院"
        assert dc["dc:language"] == "zh-CN"

    def test_from_detail_with_metadata(self):
        detail = _make_detail(
            title="青铜鼎",
            source_system="image_2d",
            source_id="42",
            resource_type="image_2d_cultural_object",
            format="TIFF",
            updated_at=datetime(2026, 6, 28),
            source_record={
                "management": {
                    "photographer": "张三",
                    "shooting_content": "青铜鼎正面拍摄",
                    "shooting_date": "2026-05-15",
                },
                "profile": {
                    "object_name": "青铜鼎",
                    "era": "商代",
                },
                "rights": {
                    "copyright_status": "故宫所有",
                    "usage_restrictions": "禁止商业用途",
                },
            },
        )
        result = from_unified_resource_detail(detail)
        dc = result["dublin_core"]
        assert dc["dc:creator"] == "张三"
        assert dc["dc:date"] == "2026-05-15"
        assert dc["dc:rights"] == "故宫所有；禁止商业用途"
        assert "dc:description" in dc

    def test_photographer_fallback_to_default_creator(self):
        """When no photographer, config default should be used."""
        detail = _make_detail(
            title="No Photo",
            source_system="image_2d",
            source_id="0",
            resource_type="image",
            updated_at=datetime(2026, 1, 1),
        )
        result = from_unified_resource_detail(detail, config={"default_creator": "故宫博物院资料信息部"})
        dc = result["dublin_core"]
        assert dc["dc:creator"] == "故宫博物院资料信息部"

    def test_dc_format_combines_fields(self):
        detail = _make_detail(
            title="Format Test",
            source_system="three_d",
            source_id="abc",
            resource_type="model",
            format="OBJ",
            updated_at=datetime(2026, 6, 1),
            source_record={"management": {}, "profile": {}},
        )
        result = from_unified_resource_detail(detail)
        dc = result["dublin_core"]
        assert "OBJ" in dc.get("dc:format", "")


# ── Test helpers ─────────────────────────────────────────────────────


class _FakeDetail:
    """Minimal mock of a UnifiedResourceDetail for testing."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def _make_detail(
    title: str = "",
    source_system: str = "",
    source_id: str = "",
    resource_type: str = "",
    format: str | None = None,
    updated_at: datetime | None = None,
    source_record: dict | None = None,
) -> _FakeDetail:
    return _FakeDetail(
        title=title or "Untitled",
        source_system=source_system,
        source_id=source_id,
        resource_type=resource_type,
        format=format,
        mime_type=format,
        resolution="6000x4000" if format else None,
        updated_at=updated_at or datetime(2026, 1, 1),
        source_record=source_record or {},
    )
