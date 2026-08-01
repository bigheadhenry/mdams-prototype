from pathlib import Path

import pytest

from app.models import Asset, ImageIngestSheet, ImageRecord, ThreeDAsset, ThreeDDigitalObject
from app.platform import image_source, three_d_source
from app.services.three_d_demo_assets import DEMO_THREE_D_ASSETS, seed_demo_three_d_assets
from app.services.two_d_demo_assets import DEMO_TWO_D_OBJECT_IDS, seed_demo_two_d_assets


pytestmark = [pytest.mark.system, pytest.mark.integration]


def test_startup_demo_datasets_are_complete_visible_and_searchable(db_session, test_upload_dir):
    seed_demo_two_d_assets(db_session)
    seed_demo_three_d_assets(db_session)

    assert len(DEMO_TWO_D_OBJECT_IDS) == 20
    assert len(set(DEMO_TWO_D_OBJECT_IDS)) == 20
    assert db_session.query(Asset).count() == 20
    assert db_session.query(ImageRecord).count() == 20
    assert db_session.query(ImageIngestSheet).count() == 1
    assert image_source.list_source_summary(db_session).resource_count == 20

    two_d_results = image_source.list_unified_resources(db_session, q="Ganymede")
    assert len(two_d_results) == 1
    assert two_d_results[0].preview_enabled is True

    for asset in db_session.query(Asset).all():
        assert Path(asset.file_path).is_file()
        assert asset.status == "ready"
        assert set(asset.metadata_info) >= {
            "core",
            "management",
            "technical",
            "profile",
            "rights",
            "rights_display",
            "raw_metadata",
        }
        assert asset.metadata_info["technical"]["fixity_sha256"]
        assert asset.metadata_info["rights"]["license"] == "CC0 1.0"
        assert asset.metadata_info["raw_metadata"]["source_record"]["objectID"] in DEMO_TWO_D_OBJECT_IDS

    unique_three_d_objects = {sample.object_number for sample in DEMO_THREE_D_ASSETS}
    assert len(unique_three_d_objects) == 20
    assert db_session.query(ThreeDDigitalObject).count() == 20
    assert db_session.query(ThreeDAsset).count() == len(DEMO_THREE_D_ASSETS) == 22
    assert three_d_source.list_source_summary(db_session).resource_count == 20

    three_d_results = three_d_source.list_unified_resources(db_session, q="Rigged Figure")
    assert len(three_d_results) == 1
    assert three_d_results[0].preview_enabled is True
    rigged_source_id = three_d_results[0].source_id.removeprefix("object-")
    rigged_detail = three_d_source.get_unified_resource(int(rigged_source_id), db_session)
    assert rigged_detail.rights_display.license == "CC BY 4.0"
    assert rigged_detail.rights_display.license_url == "https://creativecommons.org/licenses/by/4.0/"
    assert rigged_detail.rights_display.allow_derivatives is True

    for asset in db_session.query(ThreeDAsset).all():
        assert Path(asset.file_path).is_file()
        assert asset.status == "ready"
        assert asset.files
        assert all(Path(file_record.file_path).is_file() for file_record in asset.files)
        assert all(file_record.sha256 for file_record in asset.files)
        assert set(asset.metadata_info) >= {
            "core",
            "management",
            "collection",
            "technical",
            "profile",
            "preservation",
            "rights",
            "raw_metadata",
        }

    # Re-running startup seeding updates the same records instead of duplicating them.
    seed_demo_two_d_assets(db_session)
    seed_demo_three_d_assets(db_session)
    assert db_session.query(Asset).count() == 20
    assert db_session.query(ImageRecord).count() == 20
    assert db_session.query(ThreeDDigitalObject).count() == 20
    assert db_session.query(ThreeDAsset).count() == 22
