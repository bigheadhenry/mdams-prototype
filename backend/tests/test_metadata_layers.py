import pytest

from app.services.metadata_layers import build_metadata_layers, get_fixity_sha256, get_original_file_path


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def test_build_metadata_layers_defaults_to_other_when_no_object_metadata():
    layers = build_metadata_layers(
        asset_id=12,
        asset_filename="sample.jpg",
        asset_file_path="/tmp/sample.jpg",
        asset_file_size=1024,
        asset_mime_type="image/jpeg",
        asset_status="ready",
        asset_resource_type="image_2d_cultural_object",
        metadata={
            "width": 800,
            "height": 600,
            "ingest_method": "upload",
        },
    )

    assert layers["schema_version"] == "2.0"
    assert layers["core"]["resource_id"] == "asset-12"
    assert layers["core"]["title"] == "sample.jpg"
    assert layers["profile"]["key"] == "other"
    assert layers["profile"]["label"] == "其他"
    assert layers["technical"]["width"] == 800
    assert layers["technical"]["height"] == 600
    assert layers["technical"]["original_file_name"] == "sample.jpg"
    assert get_original_file_path(layers) is None


def test_build_metadata_layers_detects_business_activity_profile():
    layers = build_metadata_layers(
        asset_id=21,
        asset_filename="activity.png",
        asset_file_path="/tmp/activity.png",
        asset_file_size=2048,
        asset_mime_type="image/png",
        asset_status="ready",
        asset_resource_type="image_2d_cultural_object",
        metadata={
            "主要地点": "太和殿",
            "主要人物": "工作人员",
            "拍摄/制作内容": "业务活动记录",
        },
    )

    assert layers["profile"]["key"] == "business_activity"
    assert layers["profile"]["fields"]["main_location"] == "太和殿"
    assert layers["profile"]["fields"]["main_person"] == "工作人员"
    assert layers["management"]["capture_content"] == "业务活动记录"


def test_build_metadata_layers_detects_movable_artifact_profile():
    layers = build_metadata_layers(
        asset_id=24,
        asset_filename="artifact.jpg",
        asset_file_path="/tmp/artifact.jpg",
        asset_file_size=4096,
        asset_mime_type="image/jpeg",
        asset_status="ready",
        asset_resource_type="image_2d_cultural_object",
        metadata={
            "文物号": "故00154701",
            "文物名称": "乾隆款粉彩九桃天球瓶",
            "文物类别": "陶瓷",
        },
    )

    assert layers["profile"]["key"] == "movable_artifact"
    assert layers["profile"]["fields"]["object_number"] == "故00154701"
    assert layers["profile"]["fields"]["object_name"] == "乾隆款粉彩九桃天球瓶"
    assert layers["profile"]["fields"]["object_category"] == "陶瓷"


def test_metadata_helpers_read_layered_values():
    layers = build_metadata_layers(
        asset_id=33,
        asset_filename="converted.tiff",
        asset_file_path="/tmp/converted.tiff",
        asset_file_size=4096,
        asset_mime_type="image/tiff",
        asset_status="ready",
        asset_resource_type="image_2d_cultural_object",
        metadata={
            "fixity_sha256": "abc123",
            "original_file_path": "/tmp/original.psb",
            "width": 1200,
            "height": 900,
        },
    )

    assert get_fixity_sha256(layers) == "abc123"
    assert get_original_file_path(layers) == "/tmp/original.psb"
