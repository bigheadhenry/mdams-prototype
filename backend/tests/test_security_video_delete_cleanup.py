"""Tests for [H-5] Video delete physical file cleanup.

Verifies that deleting a video asset also removes the physical file from disk.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestVideoDeleteCleanup:
    """Verify delete_video_asset removes the physical file."""

    @patch("app.routers.video.get_db")
    @patch("app.routers.video.require_permission")
    def test_delete_removes_physical_file(self, _mock_perm, mock_get_db):
        """Physical file should be removed when video asset is deleted."""
        from app.routers.video import delete_video_asset

        # Create a temporary file to simulate the video
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            tmp.write(b"fake video data")
            tmp_path = tmp.name

        try:
            # Mock the database asset
            mock_db = MagicMock()
            mock_asset = MagicMock()
            mock_asset.file_path = tmp_path
            mock_db.query.return_value.filter.return_value.first.return_value = mock_asset

            # Call the endpoint
            delete_video_asset(asset_id=1, db=mock_db, _user=MagicMock())

            # Verify the file was deleted
            assert not Path(tmp_path).exists()
            # Verify DB delete was called
            mock_db.delete.assert_called_once_with(mock_asset)
            mock_db.commit.assert_called_once()
        finally:
            # Cleanup in case test fails
            Path(tmp_path).unlink(missing_ok=True)

    @patch("app.routers.video.get_db")
    @patch("app.routers.video.require_permission")
    def test_delete_handles_missing_file_gracefully(self, _mock_perm, mock_get_db):
        """Delete should succeed even if physical file is already gone."""
        from app.routers.video import delete_video_asset

        mock_db = MagicMock()
        mock_asset = MagicMock()
        mock_asset.file_path = "/nonexistent/path/video.mp4"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_asset

        # Should not raise even though file doesn't exist
        result = delete_video_asset(asset_id=1, db=mock_db, _user=MagicMock())

        assert result == {"ok": True}
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("app.routers.video.get_db")
    @patch("app.routers.video.require_permission")
    def test_delete_handles_none_file_path(self, _mock_perm, mock_get_db):
        """Delete should succeed when file_path is None."""
        from app.routers.video import delete_video_asset

        mock_db = MagicMock()
        mock_asset = MagicMock()
        mock_asset.file_path = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_asset

        result = delete_video_asset(asset_id=1, db=mock_db, _user=MagicMock())

        assert result == {"ok": True}
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
