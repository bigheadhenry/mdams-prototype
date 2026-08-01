from pathlib import Path

import pytest

from app.models import VideoAsset
from app.platform import video_source
from app.services.video_seed import DEMO_VIDEO_ASSETS, NASA_MEDIA_USAGE_URL, seed_demo_video_asset


pytestmark = [pytest.mark.system, pytest.mark.integration]


def test_nasa_video_dataset_is_complete_visible_and_searchable(db_session, test_upload_dir):
    seed_demo_video_asset(db_session)

    assert len(DEMO_VIDEO_ASSETS) == 5
    assert len({sample.nasa_id for sample in DEMO_VIDEO_ASSETS}) == 5
    assert db_session.query(VideoAsset).count() == 5
    assert video_source.list_source_summary(db_session).resource_count == 5

    assets = db_session.query(VideoAsset).order_by(VideoAsset.id).all()
    for asset in assets:
        assert Path(asset.file_path).is_file()
        assert asset.status == "ready"
        assert asset.duration_seconds and asset.duration_seconds > 0
        assert asset.width and asset.width > 0
        assert asset.height and asset.height > 0
        layers = asset.metadata_info
        assert set(layers) >= {
            "core",
            "management",
            "technical",
            "profile",
            "rights",
            "rights_display",
            "raw_metadata",
        }
        assert layers["technical"]["checksum"]
        assert layers["technical"]["frame_rate"] > 0
        assert layers["technical"]["frame_count"] > 0
        assert Path(layers["technical"]["poster_file_path"]).is_file()
        assert layers["rights"]["license"] == "NASA Media Usage Guidelines"
        assert layers["rights"]["license_url"] == NASA_MEDIA_USAGE_URL
        assert layers["rights"]["allow_derivatives"] is True
        assert layers["raw_metadata"]["search_record_response"]
        assert layers["raw_metadata"]["asset_manifest_response"]

    results = video_source.list_unified_resources(db_session, q="Gateway")
    assert len(results) == 1
    assert results[0].preview_enabled is True
    assert results[0].thumbnail_url.endswith("/poster")

    detail = video_source.get_unified_resource(int(results[0].source_id), db_session)
    assert detail.rights_display.license == "NASA Media Usage Guidelines"
    assert detail.rights_display.license_url == NASA_MEDIA_USAGE_URL
    assert detail.rights_display.allow_derivatives is True
    assert detail.source_record["technical"]["checksum"]
    assert detail.source_record["raw_metadata"]["nasa_id"] == "Gateway - Lunar Space Station Trailer"

    seed_demo_video_asset(db_session)
    assert db_session.query(VideoAsset).count() == 5
