import pytest

from app.models import ThreeDAsset
from app.services.three_d_production import seed_three_d_production_records


pytestmark = [pytest.mark.unit, pytest.mark.integration]


def test_seed_three_d_production_records_creates_ordered_events(db_session):
    asset = ThreeDAsset(
        filename="sample.glb",
        file_path="/tmp/sample.glb",
        file_size=1024,
        mime_type="model/gltf-binary",
        status="ready",
        resource_type="three_d_model",
        metadata_info={"core": {"title": "Sample 3D Asset"}},
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)

    seed_three_d_production_records(
        db_session,
        asset,
        saved_files=[
            {"role": "model", "role_label": "三维模型", "file_size": 512},
            {"role": "oblique_photo", "role_label": "倾斜摄影图像", "file_size": 256},
        ],
        manifest_path="/tmp/sample/manifest.json",
        preview_ready=True,
        preservation_status="preserved",
        storage_tier="archive",
    )
    db_session.commit()
    db_session.refresh(asset)

    assert len(asset.production_records) == 5
    assert [record.stage for record in asset.production_records] == [
        "ingest",
        "processing",
        "processing",
        "publish",
        "preservation",
    ]
    assert asset.production_records[0].metadata_info["file_count"] == 2
    assert asset.production_records[2].evidence == "/tmp/sample/manifest.json"
    assert asset.production_records[-1].metadata_info["preservation_status"] == "preserved"
