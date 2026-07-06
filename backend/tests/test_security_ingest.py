"""Security tests for ingest path traversal, debug endpoint, and SIP auth.

Covers audit issues:
  C-1: Path traversal in SIP ingest filename
  C-2: Unauthenticated /debug/files endpoint
  C-3: Unauthenticated SIP ingest endpoint
"""

import os

import pytest

from app.routers.ingest import _sanitize_filename

pytestmark = [pytest.mark.integration, pytest.mark.contract]


# ---------------------------------------------------------------------------
# C-1: _sanitize_filename tests (unit-level, no DB needed)
# ---------------------------------------------------------------------------


class TestSanitizeFilename:
    """Verify _sanitize_filename prevents path traversal and edge cases."""

    def test_rejects_parent_traversal(self):
        assert ".." not in _sanitize_filename("../../etc/passwd")

    def test_rejects_slash_traversal(self):
        result = _sanitize_filename("subdir/secret/file.jpg")
        assert "/" not in result
        assert "\\" not in result

    def test_strips_directory_components(self):
        assert _sanitize_filename("/var/data/test.jpg") == "test.jpg"

    def test_removes_null_bytes(self):
        result = _sanitize_filename("file\x00name.jpg")
        assert "\x00" not in result

    def test_replaces_unsafe_characters(self):
        result = _sanitize_filename("file name!@#.jpg")
        assert " " not in result
        assert "!" not in result
        assert "@" not in result

    def test_preserves_dashes_and_underscores(self):
        result = _sanitize_filename("my-file_name.jpg")
        assert result == "my-file_name.jpg"

    def test_fallback_for_none(self):
        assert _sanitize_filename(None) == "upload.bin"

    def test_fallback_for_empty(self):
        assert _sanitize_filename("") == "upload.bin"

    def test_fallback_for_dot(self):
        assert _sanitize_filename(".") == "upload.bin"

    def test_fallback_for_dotdot(self):
        assert _sanitize_filename("..") == "upload.bin"

    def test_normal_filename_unchanged(self):
        assert _sanitize_filename("scan_001.tif") == "scan_001.tif"

    def test_chinese_filename_sanitized(self):
        # Chinese chars are replaced by underscores (not word chars in regex)
        result = _sanitize_filename("测试图片.jpg")
        assert ".." not in result
        # Should not be empty
        assert len(result) > 0

    def test_traversal_with_encoding(self):
        """Even encoded traversal sequences should be neutralized."""
        result = _sanitize_filename("..%2F..%2Fetc%2Fpasswd")
        assert ".." not in result
        assert "/" not in result
