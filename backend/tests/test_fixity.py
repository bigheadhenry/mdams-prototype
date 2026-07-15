from pathlib import Path

import pytest

from app.services.fixity import calculate_sha256, verify_path


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def test_fixity_records_then_verifies_and_detects_mismatch(tmp_path: Path):
    candidate = tmp_path / "sample.bin"
    candidate.write_bytes(b"original")

    baseline = verify_path(candidate, None)
    assert baseline.status == "recorded"
    assert baseline.expected_sha256 == calculate_sha256(candidate)

    verified = verify_path(candidate, baseline.expected_sha256)
    assert verified.status == "verified"

    candidate.write_bytes(b"changed")
    mismatch = verify_path(candidate, baseline.expected_sha256)
    assert mismatch.status == "mismatch"
    assert mismatch.actual_sha256 != mismatch.expected_sha256


def test_fixity_reports_missing_file(tmp_path: Path):
    result = verify_path(tmp_path / "missing.bin", "abc")
    assert result.status == "missing"
    assert result.actual_sha256 is None
