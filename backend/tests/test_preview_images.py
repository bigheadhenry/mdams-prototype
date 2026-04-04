from pathlib import Path

from PIL import Image

from app import config as app_config
from app.models import Asset
from app.services.preview_images import ensure_preview_image, get_preview_image_path


def _create_asset(db_session, *, asset_id: int, filename: str, file_path: str) -> Asset:
    asset = Asset(
        id=asset_id,
        filename=filename,
        file_path=file_path,
        file_size=0,
        mime_type="image/jpeg",
        visibility_scope="open",
        collection_object_id=None,
        status="ready",
        resource_type="image_2d_cultural_object",
        metadata_info={
            "core": {"title": filename},
            "technical": {},
            "management": {},
            "profile": {"key": "other", "label": "其他", "sheet": "其他", "fields": {}},
            "raw_metadata": {},
        },
    )
    db_session.add(asset)
    db_session.commit()
    db_session.refresh(asset)
    return asset


def _write_image(path: Path, color: str, size: tuple[int, int]) -> None:
    image = Image.new("RGB", size, color)
    image.save(path, format="JPEG", quality=95)


def test_preview_image_path_changes_when_source_changes(db_session, tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(upload_dir))

    source_path = upload_dir / "sample.jpg"
    _write_image(source_path, "red", (320, 240))
    asset = _create_asset(db_session, asset_id=9001, filename="sample.jpg", file_path=str(source_path))

    first_preview = ensure_preview_image(asset)
    assert first_preview is not None
    assert Path(first_preview).exists()
    assert first_preview == get_preview_image_path(asset, str(source_path))

    source_path_v2 = upload_dir / "sample-v2.jpg"
    _write_image(source_path_v2, "blue", (480, 360))
    asset.file_path = str(source_path_v2)
    db_session.commit()

    second_preview = ensure_preview_image(asset)
    assert second_preview is not None
    assert Path(second_preview).exists()
    assert second_preview == get_preview_image_path(asset, str(source_path_v2))
    assert second_preview != first_preview
