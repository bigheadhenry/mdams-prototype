from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from .. import config
from ..models import VideoAsset
from .video_metadata import build_video_metadata_layers

DEMO_VIDEO_FILENAME = "景泰款掐丝珐琅莲托杂宝纹螭耳熏炉.mp4"
DEMO_VIDEO_TITLE = "景泰款掐丝珐琅莲托杂宝纹螭耳熏炉"

# Try multiple possible source locations for the demo video
_DEMO_VIDEO_SOURCE_CANDIDATES = [
    # Inside Docker: /app/uploads is mounted from host uploads/
    Path("/app/uploads/videos") / DEMO_VIDEO_FILENAME,
    # Windows dev machine absolute path
    Path(r"C:\Users\bighe\OneDrive\AI\Codex\mdams-prototype\reference") / DEMO_VIDEO_FILENAME,
    # Relative to backend directory (project root / reference)
    Path(__file__).resolve().parents[3] / "reference" / DEMO_VIDEO_FILENAME,
]


def _find_demo_video() -> Path | None:
    """Find the demo video file from candidate locations."""
    for candidate in _DEMO_VIDEO_SOURCE_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def _video_dir() -> Path:
    return Path(config.UPLOAD_DIR) / "videos"


def seed_demo_video_asset(db: Session) -> None:
    """Register the demo video asset if not already present."""
    _video_dir().mkdir(parents=True, exist_ok=True)

    existing = db.query(VideoAsset).filter(
        VideoAsset.filename == DEMO_VIDEO_FILENAME
    ).first()
    if existing is not None:
        return

    demo_source = _find_demo_video()
    if demo_source is None:
        print(f"[video_seed] Demo video not found. Looked in: {_DEMO_VIDEO_SOURCE_CANDIDATES}")
        return

    file_size = demo_source.stat().st_size
    mime_type = "video/mp4"
    dest_path = _video_dir() / DEMO_VIDEO_FILENAME

    if not dest_path.exists():
        shutil.copy2(str(demo_source), str(dest_path))

    asset = VideoAsset(
        filename=DEMO_VIDEO_FILENAME,
        file_path=str(dest_path),
        file_size=file_size,
        mime_type=mime_type,
        status="ready",
        resource_type="video_cultural_object",
        process_message="演示视频已登记",
        metadata_info={
            "title": DEMO_VIDEO_TITLE,
            "description": "景泰款掐丝珐琅莲托杂宝纹螭耳熏炉 — 演示视频样本",
        },
    )
    db.add(asset)
    db.flush()

    # Build metadata layers
    layers = build_video_metadata_layers(
        asset_id=asset.id,
        asset_filename=asset.filename,
        asset_file_path=asset.file_path,
        asset_file_size=asset.file_size,
        asset_mime_type=asset.mime_type,
        asset_status=asset.status,
        asset_resource_type=asset.resource_type,
        asset_created_at=asset.created_at,
        metadata=asset.metadata_info,
    )
    asset.metadata_info = layers
    db.commit()
    print(f"[video_seed] Registered demo video: {DEMO_VIDEO_TITLE} (id={asset.id})")
