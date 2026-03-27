import asyncio
from io import BytesIO

from fastapi import UploadFile
from PIL import Image

from app import config as app_config
from app.models import Asset
from app.platform import image_source
from app.routers import assets as assets_router
from app.routers import platform as platform_router


def _make_png_bytes():
    image = Image.new("RGB", (12, 10), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


async def _upload_sample(db_session, upload_dir, *, filename: str = "platform-sample.png", metadata_info=None):
    file = UploadFile(file=_make_png_bytes(), filename=filename)
    uploaded = await assets_router.upload_file(file=file, db=db_session)
    assert (upload_dir / filename).exists()
    if metadata_info is not None:
        asset = db_session.get(Asset, uploaded.id)
        assert asset is not None
        asset.metadata_info = metadata_info
        db_session.commit()
    return uploaded


def test_platform_resource_directory_maps_image_subsystem(db_session, test_upload_dir, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))

    uploaded = asyncio.run(_upload_sample(db_session, test_upload_dir))
    profile_uploaded = asyncio.run(
        _upload_sample(
            db_session,
            test_upload_dir,
            filename="platform-profile.png",
            metadata_info={
                "object_number": "故00154701",
                "object_name": "青花瓷瓶",
            },
        )
    )

    sources = platform_router.get_sources(db=db_session)
    assert len(sources) == 2
    assert sources[0].source_system == image_source.SOURCE_SYSTEM
    assert sources[0].source_label == "二维影像子系统"
    assert sources[0].resource_count == 2
    three_d_summary = next(source for source in sources if source.source_system == "three_d")
    assert three_d_summary.resource_count == 0

    resources = platform_router.get_resources(db=db_session)
    assert len(resources) == 2

    resource = next(item for item in resources if item.id == f"{image_source.SOURCE_SYSTEM}:{uploaded.id}")
    assert resource.source_id == str(uploaded.id)
    assert resource.preview_enabled is True
    assert resource.profile_key == "other"
    assert resource.profile_label == "其他"
    assert resource.detail_url.endswith(resource.id)

    profile_resource = next(
        item for item in resources if item.id == f"{image_source.SOURCE_SYSTEM}:{profile_uploaded.id}"
    )
    assert profile_resource.source_id == str(profile_uploaded.id)
    assert profile_resource.profile_key == "movable_artifact"
    assert profile_resource.profile_label == "可移动文物"

    detail = platform_router.get_resource(resource_id=resource.id, db=db_session)
    assert detail.id == resource.id
    assert detail.source_label == "二维影像子系统"
    assert detail.source_record is not None
    assert detail.source_record.id == uploaded.id
    assert detail.source_detail_url == f"/api/assets/{uploaded.id}"
    assert detail.source_record.structure.primary_file.filename == "platform-sample.png"
    assert detail.profile_key == "other"
    assert detail.profile_label == "其他"

    filtered = platform_router.get_resources(q="platform-sample", db=db_session)
    assert len(filtered) == 1
    assert filtered[0].id == resource.id

    status_filtered = platform_router.get_resources(status="ready", db=db_session)
    assert len(status_filtered) == 2
    assert all(item.status == "ready" for item in status_filtered)

    profile_filtered = platform_router.get_resources(profile_key="movable_artifact", db=db_session)
    assert len(profile_filtered) == 1
    assert profile_filtered[0].id == profile_resource.id

    other_filtered = platform_router.get_resources(profile_key="other", db=db_session)
    assert len(other_filtered) == 1
    assert other_filtered[0].id == resource.id

    db_session.query(Asset).delete()
    db_session.commit()
