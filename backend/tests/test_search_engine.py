"""Integration tests for the search engine adapter and platform search."""

import pytest
from datetime import datetime, timezone

from app.services.search_engine import (
    SearchDocument,
    SearchQuery,
    SearchResponse,
    SearchResult,
    SearchEngineAdapter,
)
from app.services.search_engine.meilisearch_adapter import (
    MeilisearchAdapter,
    _build_filter_expression,
    _doc_to_dict,
)


# ── Unit: Filter expression builder ──────────────────────────────────


class TestFilterExpression:
    def test_single_field(self):
        expr = _build_filter_expression({"source_system": "image_2d"})
        assert expr == "(source_system = 'image_2d')"

    def test_boolean_field(self):
        expr = _build_filter_expression({"preview_enabled": True})
        assert "(preview_enabled = true)" in expr

    def test_list_field(self):
        expr = _build_filter_expression({"status": ["active", "draft"]})
        assert "status IN" in expr
        assert "'active'" in expr
        assert "'draft'" in expr

    def test_empty_filter(self):
        expr = _build_filter_expression({})
        assert expr is None

    def test_mixed_filter(self):
        expr = _build_filter_expression({
            "source_system": "image_2d",
            "status": "active",
            "preview_enabled": True,
        })
        assert "source_system" in expr
        assert "status" in expr
        assert "preview_enabled = true" in expr
        assert " AND " in expr


# ── Unit: SearchDocument → dict conversion ───────────────────────────


class TestDocToDict:
    def test_minimal(self):
        doc = SearchDocument(
            id="image_2d:1",
            source_system="image_2d",
            source_id="1",
            source_label="二维影像",
            title="Test",
            resource_type="image",
            status="active",
            preview_enabled=False,
            updated_at="2026-01-01T00:00:00",
        )
        d = _doc_to_dict(doc)
        assert d["id"] == "image_2d:1"
        assert d["title"] == "Test"
        assert d["search_text"] == ""

    def test_with_search_text(self):
        doc = SearchDocument(
            id="three_d:abc",
            source_system="three_d",
            source_id="abc",
            source_label="三维资源",
            title="唐三彩",
            resource_type="model",
            status="active",
            preview_enabled=True,
            updated_at="2026-06-01T00:00:00",
            search_text="唐三彩 三维资源 model",
        )
        d = _doc_to_dict(doc)
        assert d["search_text"] == "唐三彩 三维资源 model"

    def test_full_fields(self):
        doc = SearchDocument(
            id="video:v1",
            source_system="video",
            source_id="v1",
            source_label="视频",
            title="故宫宣传片",
            resource_type="video",
            profile_key="promo",
            profile_label="宣传片",
            status="active",
            preview_enabled=True,
            thumbnail_url="/thumb/v1.jpg",
            updated_at="2026-06-28T00:00:00",
            resolution="1920x1080",
            format="MP4",
            era="当代",
            main_person="张导",
            main_location="故宫",
            manifest_url="/manifest/v1",
            detail_url="/detail/video/v1",
            search_text="故宫宣传片 视频",
        )
        d = _doc_to_dict(doc)
        assert d["resolution"] == "1920x1080"
        assert d["manifest_url"] == "/manifest/v1"
        assert d["detail_url"] == "/detail/video/v1"


# ── Meilisearch integration (requires running Meilisearch) ────────────


meili_available = pytest.mark.skipif(
    "not os.environ.get('MEILI_URL') and not os.environ.get('CI')",
    reason="Meilisearch not available in test environment",
)


class TestMeilisearchIntegration:
    """Integration tests that require a running Meilisearch instance.

    These are skipped by default. Run with MEILI_URL=http://localhost:7700
    or in CI (where Meilisearch is provided as a service).
    """

    @meili_available
    def test_health(self):
        adapter = MeilisearchAdapter()
        assert adapter.health() is True

    @meili_available
    def test_index_and_search(self):
        adapter = MeilisearchAdapter()
        adapter.create_index_if_missing()

        # Index a doc
        doc = SearchDocument(
            id="test:1",
            source_system="test",
            source_id="1",
            source_label="测试来源",
            title="测试文档",
            resource_type="test",
            status="active",
            preview_enabled=True,
            updated_at="2026-06-28T00:00:00",
        )
        adapter.index_document(doc)

        # Search it back
        query = SearchQuery(q="测试")
        response = adapter.search(query)
        assert response.total >= 1
        assert any("测试" in h.document.get("title", "") for h in response.items)

        # Cleanup
        adapter.delete_document("test:1")

    @meili_available
    def test_filter_search(self):
        adapter = MeilisearchAdapter()
        adapter.create_index_if_missing()

        docs = [
            SearchDocument(
                id=f"test:{i}",
                source_system="filter_test",
                source_id=str(i),
                source_label="过滤测试",
                title=f"Item {i}",
                resource_type="image" if i % 2 == 0 else "model",
                status="active",
                preview_enabled=True,
                updated_at="2026-06-28T00:00:00",
            )
            for i in range(3)
        ]
        adapter.index_documents(docs)

        query = SearchQuery(filter={"resource_type": "image"})
        response = adapter.search(query)
        assert response.total >= 1

        for d in docs:
            adapter.delete_document(d.id)

    @meili_available
    def test_count_and_clear(self):
        adapter = MeilisearchAdapter()
        adapter.create_index_if_missing()
        adapter.clear()
        assert adapter.count() == 0


# ── Mock adapter for unit testing fallback behavior ──────────────────


class MockSearchEngine(SearchEngineAdapter):
    """In-memory mock for testing the search interface without Meilisearch."""

    def __init__(self):
        self._docs: dict[str, dict] = {}

    def index_document(self, doc: SearchDocument) -> None:
        self._docs[doc.id] = _doc_to_dict(doc)

    def index_documents(self, docs: list[SearchDocument]) -> None:
        for d in docs:
            self.index_document(d)

    def delete_document(self, doc_id: str) -> None:
        self._docs.pop(doc_id, None)

    def get_document(self, doc_id: str) -> dict | None:
        return self._docs.get(doc_id)

    def search(self, query: SearchQuery) -> SearchResponse:
        q = (query.q or "").lower()
        results = []
        for doc_id, doc in self._docs.items():
            if q and q not in doc.get("title", "").lower():
                continue
            # Apply filters
            for key, value in query.filter.items():
                if isinstance(value, list):
                    if doc.get(key) not in value:
                        break
                elif doc.get(key) != value:
                    break
            else:
                results.append(SearchResult(id=doc_id, document=doc))
        return SearchResponse(
            items=results[query.skip:query.skip + query.limit] if results else [],
            total=len(results),
        )

    def count(self) -> int:
        return len(self._docs)

    def clear(self) -> None:
        self._docs.clear()

    def health(self) -> bool:
        return True

    def create_index_if_missing(self) -> None:
        pass


class TestMockSearchEngine:
    def test_index_and_retrieve(self):
        engine = MockSearchEngine()
        doc = SearchDocument(
            id="test:1", source_system="test", source_id="1",
            source_label="测试", title="Test Doc", resource_type="doc",
            status="ok", preview_enabled=False,
            updated_at="2026-06-28T00:00:00",
        )
        engine.index_document(doc)
        assert engine.count() == 1
        assert engine.get_document("test:1") is not None

    def test_search_by_query(self):
        engine = MockSearchEngine()
        engine.index_document(SearchDocument(
            id="a:1", source_system="a", source_id="1",
            source_label="A", title="Alpha", resource_type="img",
            status="ok", preview_enabled=False,
            updated_at="2026-06-28T00:00:00",
        ))
        engine.index_document(SearchDocument(
            id="b:1", source_system="b", source_id="1",
            source_label="B", title="Beta", resource_type="img",
            status="ok", preview_enabled=False,
            updated_at="2026-06-28T00:00:00",
        ))
        resp = engine.search(SearchQuery(q="Alpha"))
        assert resp.total == 1
        assert resp.items[0].id == "a:1"

    def test_filter(self):
        engine = MockSearchEngine()
        for i in range(3):
            engine.index_document(SearchDocument(
                id=f"img:{i}", source_system="img", source_id=str(i),
                source_label="Images", title=f"Photo {i}", resource_type="image",
                status="active", preview_enabled=True,
                updated_at="2026-06-28T00:00:00",
            ))
        engine.index_document(SearchDocument(
            id="m:1", source_system="3d", source_id="1",
            source_label="3D", title="Model", resource_type="model",
            status="active", preview_enabled=True,
            updated_at="2026-06-28T00:00:00",
        ))
        resp = engine.search(SearchQuery(filter={"resource_type": "image"}))
        assert resp.total == 3

    def test_clear(self):
        engine = MockSearchEngine()
        engine.index_document(SearchDocument(
            id="x:1", source_system="x", source_id="1",
            source_label="X", title="Temp", resource_type="x",
            status="ok", preview_enabled=False,
            updated_at="2026-06-28T00:00:00",
        ))
        engine.clear()
        assert engine.count() == 0


# ── Contract tests for search result structure ────────────────────


class TestSearchResultContract:
    """验证搜索返回结构稳定"""

    def test_search_result_fields(self):
        """搜索结果包含来源、资源 ID、标题、score"""
        doc = SearchDocument(
            id="image_2d:42",
            source_system="image_2d",
            source_id="42",
            source_label="二维影像子系统",
            title="清乾隆各色釉彩大瓶",
            resource_type="image_2d_cultural_object",
            profile_key="movable_artifact",
            status="ready",
            preview_enabled=True,
            thumbnail_url="/api/assets/42/preview",
            updated_at="2026-07-06T00:00:00Z",
            manifest_url="/api/iiif/42/manifest",
            detail_url="/api/platform/resources/image_2d/42",
            search_text="清乾隆各色釉彩大瓶 二维影像子系统",
        )
        engine = MockSearchEngine()
        engine.index_document(doc)

        resp = engine.search(SearchQuery(q="釉彩"))
        assert resp.total >= 1
        for result in resp.items:
            assert result.id == "image_2d:42"
            assert result.document["source_system"] == "image_2d"
            assert result.document["source_id"] == "42"
            assert "釉彩" in result.document["title"]
            # score may be None in MockEngine
            assert "title" in result.document
            assert "source_system" in result.document
            assert "resource_type" in result.document
            assert "status" in result.document

    def test_empty_query_returns_all(self):
        """空关键词返回所有文档"""
        engine = MockSearchEngine()
        for i in range(3):
            engine.index_document(SearchDocument(
                id=f"t:{i}", source_system="t", source_id=str(i),
                source_label="T", title=f"Doc {i}", resource_type="t",
                status="ok", preview_enabled=False,
                updated_at="2026-07-06T00:00:00Z",
            ))
        resp = engine.search(SearchQuery(q=""))
        assert resp.total == 3

    def test_none_query_returns_all(self):
        """None 关键词返回所有文档"""
        engine = MockSearchEngine()
        for i in range(3):
            engine.index_document(SearchDocument(
                id=f"t:{i}", source_system="t", source_id=str(i),
                source_label="T", title=f"Doc {i}", resource_type="t",
                status="ok", preview_enabled=False,
                updated_at="2026-07-06T00:00:00Z",
            ))
        resp = engine.search(SearchQuery(q=None))
        assert resp.total == 3

    def test_search_response_has_total_and_items(self):
        """SearchResponse 必有 total 和 items"""
        resp = SearchResponse(items=[], total=0)
        assert resp.total == 0
        assert resp.items == []

    def test_facet_structure(self):
        """验证 Meilisearch 的 facetDistribution 结构"""
        # 模拟 Meilisearch facet 返回结构
        mock_facets = {
            "source_system": {"image_2d": 10, "three_d": 5, "video": 2},
            "status": {"ready": 15, "processing": 2},
            "profile_key": {"movable_artifact": 8, "other": 9},
        }
        resp = SearchResponse(items=[], total=17, facet_distribution=mock_facets)
        assert resp.facet_distribution is not None
        assert "source_system" in resp.facet_distribution
        assert resp.facet_distribution["source_system"]["image_2d"] == 10
        assert resp.facet_distribution["status"]["ready"] == 15
