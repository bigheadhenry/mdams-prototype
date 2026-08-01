from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import cv2
from sqlalchemy.orm import Session

from .. import config
from ..models import VideoAsset
from .video_metadata import build_video_metadata_layers

NASA_LIBRARY_URL = "https://images.nasa.gov/"
NASA_MEDIA_USAGE_URL = "https://www.nasa.gov/nasa-brand-center/images-and-media/"
DEMO_VIDEO_RETRIEVED_AT = "2026-07-23"


@dataclass(frozen=True)
class DemoVideoAsset:
    slug: str
    filename: str
    poster_filename: str
    nasa_id: str
    profile_key: str
    mission: str | None
    program: str | None
    topic: str
    audience: str


DEMO_VIDEO_ASSETS: tuple[DemoVideoAsset, ...] = (
    DemoVideoAsset(
        slug="gateway-lunar-station",
        filename="nasa-gateway-lunar-station.mp4",
        poster_filename="nasa-gateway-lunar-station-poster.jpg",
        nasa_id="Gateway - Lunar Space Station Trailer",
        profile_key="mission_documentary",
        mission="Artemis / Gateway",
        program="Lunar Gateway",
        topic="月球轨道空间站与深空探索",
        audience="公众、教育与科研用户",
    ),
    DemoVideoAsset(
        slug="how-big-is-space",
        filename="nasa-how-big-is-space.mp4",
        poster_filename="nasa-how-big-is-space-poster.jpg",
        nasa_id="How Big is Space",
        profile_key="science_education",
        mission=None,
        program="We Asked a NASA Expert",
        topic="宇宙尺度与空间科学",
        audience="公众与学生",
    ),
    DemoVideoAsset(
        slug="olympics-iss",
        filename="nasa-olympics-iss.mp4",
        poster_filename="nasa-olympics-iss-poster.jpg",
        nasa_id="Olympics on the International Space Station",
        profile_key="human_spaceflight",
        mission="International Space Station",
        program="ISS",
        topic="微重力环境中的载人航天生活",
        audience="公众、教育与航天爱好者",
    ),
    DemoVideoAsset(
        slug="webb-journey-ep2",
        filename="nasa-webb-journey-ep2.mp4",
        poster_filename="nasa-webb-journey-ep2-poster.jpg",
        nasa_id="Webb Journey to Space Ep2",
        profile_key="mission_documentary",
        mission="James Webb Space Telescope",
        program="JWST Journey to Space",
        topic="詹姆斯·韦布空间望远镜发射准备",
        audience="公众、教育与科研用户",
    ),
    DemoVideoAsset(
        slug="space-dangers",
        filename="nasa-space-dangers.mp4",
        poster_filename="nasa-space-dangers-poster.jpg",
        nasa_id="What Are the Dangers of Going to Space",
        profile_key="science_education",
        mission=None,
        program="We Asked a NASA Expert",
        topic="载人航天风险与空间环境",
        audience="公众与学生",
    ),
)


def _source_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "demo_assets" / "video"


def _video_dir() -> Path:
    return Path(config.UPLOAD_DIR) / "videos" / "nasa-open-media"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _source_data(record_response: dict[str, Any]) -> dict[str, Any]:
    items = ((record_response.get("collection") or {}).get("items") or [])
    if not items or not isinstance(items[0], dict):
        raise ValueError("NASA search response does not contain a collection item")
    data = items[0].get("data") or []
    if not data or not isinstance(data[0], dict):
        raise ValueError("NASA search response does not contain item metadata")
    return data[0]


def _asset_hrefs(asset_manifest: dict[str, Any]) -> list[str]:
    items = ((asset_manifest.get("collection") or {}).get("items") or [])
    return [str(item["href"]) for item in items if isinstance(item, dict) and item.get("href")]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _inspect_video(path: Path) -> dict[str, Any]:
    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise ValueError(f"Unable to inspect video: {path}")
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_rate = float(capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        fourcc_value = int(capture.get(cv2.CAP_PROP_FOURCC))
        codec = "".join(chr((fourcc_value >> (8 * index)) & 0xFF) for index in range(4)).strip("\x00")
        duration = frame_count / frame_rate if frame_rate > 0 else 0.0
    finally:
        capture.release()
    return {
        "width": width,
        "height": height,
        "frame_rate": round(frame_rate, 3),
        "frame_count": frame_count,
        "codec": codec or None,
        "duration_seconds_exact": round(duration, 3),
        "duration_seconds": max(1, round(duration)),
        "aspect_ratio": f"{width}:{height}" if width and height else None,
    }


def _selected_mobile_url(asset_manifest: dict[str, Any]) -> str:
    hrefs = _asset_hrefs(asset_manifest)
    return next((href for href in hrefs if href.lower().endswith("~mobile.mp4")), "")


def _copy_if_needed(source: Path, destination: Path) -> None:
    if not destination.exists() or source.stat().st_size != destination.stat().st_size:
        shutil.copy2(source, destination)


def seed_demo_video_asset(db: Session) -> None:
    """Create or refresh the five bundled NASA video test assets."""
    source_dir = _source_dir()
    target_dir = _video_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    registered: list[VideoAsset] = []
    for sample in DEMO_VIDEO_ASSETS:
        source_video = source_dir / sample.filename
        source_poster = source_dir / sample.poster_filename
        record_path = source_dir / "source_metadata" / f"{sample.slug}-record.json"
        manifest_path = source_dir / "source_metadata" / f"{sample.slug}-assets.json"
        for required_path in (source_video, source_poster, record_path, manifest_path):
            if not required_path.is_file():
                raise FileNotFoundError(f"Bundled demo video resource is missing: {required_path}")

        record_response = _read_json(record_path)
        asset_manifest = _read_json(manifest_path)
        nasa_data = _source_data(record_response)
        if nasa_data.get("nasa_id") != sample.nasa_id:
            raise ValueError(f"Unexpected NASA record for {sample.slug}")

        target_video = target_dir / sample.filename
        target_poster = target_dir / sample.poster_filename
        _copy_if_needed(source_video, target_video)
        _copy_if_needed(source_poster, target_poster)

        inspection = _inspect_video(target_video)
        selected_url = _selected_mobile_url(asset_manifest)
        keywords = nasa_data.get("keywords") or []
        albums = nasa_data.get("album") or []
        source_url = f"https://images.nasa.gov/details/{quote(sample.nasa_id, safe='')}"
        business_metadata = {
            "title": nasa_data.get("title") or sample.nasa_id,
            "profile_key": sample.profile_key,
            "project_name": ", ".join(str(value) for value in albums) or sample.program,
            "producer": "NASA",
            "producer_org": "National Aeronautics and Space Administration",
            "source_center": nasa_data.get("center"),
            "date_created": nasa_data.get("date_created"),
            "description": nasa_data.get("description"),
            "keywords": keywords,
            "language": "en",
            "ingest_method": "系统启动时从内置的 NASA 官方真实数据包登记",
            "record_time": DEMO_VIDEO_RETRIEVED_AT,
            "source_url": source_url,
            "mission": sample.mission,
            "program": sample.program,
            "topic": sample.topic,
            "audience": sample.audience,
            "format_name": "MP4",
            "format_version": "ISO Base Media",
            "frame_rate": inspection["frame_rate"],
            "frame_count": inspection["frame_count"],
            "codec": inspection["codec"],
            "aspect_ratio": inspection["aspect_ratio"],
            "duration_seconds_exact": inspection["duration_seconds_exact"],
            "checksum_algorithm": "SHA256",
            "checksum": _sha256(target_video),
            "poster_filename": sample.poster_filename,
            "poster_file_path": str(target_poster),
            "poster_mime_type": "image/jpeg",
            "source_variant": "NASA Image and Video Library mobile MP4",
            "source_download_url": selected_url,
            "copyright_status": "NASA/U.S. government work; generally not subject to copyright in the United States",
            "copyright_owner": "NASA",
            "rights_holder": "NASA",
            "access_scope": "公开",
            "allowed_usage": "可依 NASA Media Usage Guidelines 用于新闻、教育和信息传播用途",
            "license": "NASA Media Usage Guidelines",
            "license_url": NASA_MEDIA_USAGE_URL,
            "allow_derivatives": True,
            "usage_restrictions": "不得暗示 NASA 对商业产品、服务或活动的认可；NASA 标识、徽章和任务标识适用独立限制；涉及可识别人物时须考虑肖像权和公开权；使用前应核查单项资源署名及第三方版权说明。",
            "permission_notes": "本测试记录不构成法律许可；实际发布时应复核 NASA 官方使用政策和单项署名。",
        }
        source_metadata = {
            "provider": "NASA Image and Video Library",
            "provider_url": NASA_LIBRARY_URL,
            "rights_policy_url": NASA_MEDIA_USAGE_URL,
            "retrieved_at": DEMO_VIDEO_RETRIEVED_AT,
            "nasa_id": sample.nasa_id,
            "source_detail_url": source_url,
            "selected_asset_url": selected_url,
            "selected_asset_variant": "mobile MP4",
            "search_record_response": record_response,
            "asset_manifest_response": asset_manifest,
        }

        asset = db.query(VideoAsset).filter(VideoAsset.filename == sample.filename).first()
        if asset is None:
            asset = VideoAsset(filename=sample.filename)
            db.add(asset)
        asset.file_path = str(target_video)
        asset.file_size = target_video.stat().st_size
        asset.mime_type = "video/mp4"
        asset.status = "ready"
        asset.resource_type = "video_cultural_object"
        asset.process_message = "NASA 官方真实视频测试资源已登记"
        asset.duration_seconds = inspection["duration_seconds"]
        asset.width = inspection["width"]
        asset.height = inspection["height"]
        db.flush()
        asset.metadata_info = build_video_metadata_layers(
            asset_id=asset.id,
            asset_filename=asset.filename,
            asset_file_path=asset.file_path,
            asset_file_size=asset.file_size,
            asset_mime_type=asset.mime_type,
            asset_status=asset.status,
            asset_resource_type=asset.resource_type,
            asset_created_at=asset.created_at,
            asset_duration_seconds=asset.duration_seconds,
            asset_width=asset.width,
            asset_height=asset.height,
            metadata=business_metadata,
            source_metadata=source_metadata,
        )
        registered.append(asset)

    db.commit()
    print(f"[video_seed] Registered/refreshed {len(registered)} NASA demo videos")
