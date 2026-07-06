"""Tests for [H-4] SHA256 duplicate detection optimization.

Verifies that _duplicate_assets_for_hash uses database-level JSONB filtering
instead of loading all assets into Python memory.
"""

from unittest.mock import MagicMock, patch

import app.routers.image_records as mod


class TestDuplicateAssetsForHash:
    """Verify _duplicate_assets_for_hash query optimization."""

    def test_empty_sha256_returns_empty_list(self):
        db = MagicMock()
        assert mod._duplicate_assets_for_hash(db, "") == []
        assert mod._duplicate_assets_for_hash(db, None) == []
        db.query.assert_not_called()

    @patch.object(mod, "Asset")
    def test_uses_filter_not_full_scan(self, _mock_asset):
        """Query must call .filter() then .all(), NOT .all() then Python loop."""
        db = MagicMock()
        # Chain: db.query().filter().order_by().all()
        chain = MagicMock()
        chain.all.return_value = [MagicMock()]
        chain.order_by.return_value = chain
        chain.filter.return_value = chain
        db.query.return_value = chain

        result = mod._duplicate_assets_for_hash(db, "abc123")

        # .filter() must be called (DB-level filtering, not Python-side)
        chain.filter.assert_called_once()
        # .order_by() must be called
        chain.order_by.assert_called_once()
        # Result comes from .all()
        assert len(result) == 1
