import pytest

from app.services.derivative_policy import build_derivative_policy, infer_derivative_policy_from_metadata


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def test_build_derivative_policy_marks_large_tiff_for_pyramidal_copy():
    policy = build_derivative_policy(
        filename="scan.tif",
        mime_type="image/tiff",
        file_size=120 * 1024 * 1024,
        width=9000,
        height=7000,
    )

    assert policy["derivative_strategy"] == "generate_pyramidal_tiff"
    assert policy["derivative_priority"] == "recommended"
    assert policy["derivative_target_format"] == "image/tiff"
    assert policy["derivative_rule_id"] == "tiff_large_pyramidal_tiled_copy"


def test_build_derivative_policy_keeps_normal_jpeg():
    policy = build_derivative_policy(
        filename="photo.jpg",
        mime_type="image/jpeg",
        file_size=8 * 1024 * 1024,
        width=3200,
        height=2400,
    )

    assert policy["derivative_strategy"] == "keep_original"
    assert policy["derivative_priority"] == "none"
    assert policy["derivative_rule_id"] == "jpeg_keep_original"


def test_infer_derivative_policy_reads_layered_metadata():
    policy = infer_derivative_policy_from_metadata(
        {
            "technical": {
                "original_file_name": "asset.psb",
                "format_name": "application/octet-stream",
                "file_size": 80 * 1024 * 1024,
                "width": 8000,
                "height": 6000,
            }
        }
    )

    assert policy["derivative_rule_id"] == "tiff_large_pyramidal_tiled_copy"
    assert policy["derivative_strategy"] == "generate_pyramidal_tiff"
