from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image
from sqlalchemy.orm import Session

from .. import config
from ..models import Asset, ImageIngestSheet, ImageRecord
from .metadata_layers import build_metadata_layers


DEMO_TWO_D_OBJECT_IDS = (
    466105,
    453351,
    456949,
    51776,
    465966,
    24860,
    464023,
    315786,
    506174,
    81136,
    313153,
    38059,
    447107,
    453369,
    448369,
    450084,
    256975,
    256976,
    465818,
    207258,
)

DATASET_SHEET_NO = "DEMO-2D-MET-OA-2026"
DATASET_TIMESTAMP = "2026-07-23T00:00:00+08:00"
OPEN_ACCESS_POLICY_URL = "https://www.metmuseum.org/about-the-met/policies-and-documents/open-access"


def _asset_source_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "demo_assets" / "two_d"


def _target_dir() -> Path:
    return Path(config.UPLOAD_DIR) / "two-d" / "met-open-access"


def _load_source_record(object_id: int) -> dict[str, Any]:
    metadata_path = _asset_source_dir() / "source_metadata" / f"met-{object_id}.json"
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def _title(source: dict[str, Any]) -> str:
    title = str(source.get("title") or source.get("objectName") or "Untitled")
    accession_number = str(source.get("accessionNumber") or source.get("objectID") or "")
    return f"{title}（The Met {accession_number}）"


def _object_category(source: dict[str, Any]) -> str:
    text = " ".join(
        str(source.get(key) or "")
        for key in ("objectName", "medium", "department", "title")
    ).lower()
    if any(token in text for token in ("painting", "watercolor", "album")):
        return "绘画"
    if any(token in text for token in ("manuscript", "folio", "writing tablet")):
        return "古籍"
    if any(token in text for token in ("shirt", "tunic", "waistcoat", "textile", "silk", "skirt")):
        return "织绣"
    if any(token in text for token in ("jewelry", "brooch", "pendant", "gold", "silver")):
        return "金银器"
    if "porcelain" in text or "ceramic" in text or "earthenware" in text:
        return "陶瓷"
    return "其他工艺"


def _source_tags(source: dict[str, Any]) -> list[str]:
    tags = [
        str(source.get("objectName") or ""),
        str(source.get("department") or ""),
        str(source.get("culture") or ""),
        _object_category(source),
        "The Met Open Access",
        "真实数据",
    ]
    for item in source.get("tags") or []:
        if isinstance(item, dict) and item.get("term"):
            tags.append(str(item["term"]))
    return list(dict.fromkeys(tag for tag in tags if tag))


def _build_metadata(
    *,
    source: dict[str, Any],
    target_file: Path,
    width: int,
    height: int,
    checksum: str,
) -> dict[str, Any]:
    object_id = int(source["objectID"])
    object_number = str(source.get("accessionNumber") or object_id)
    object_name = str(source.get("title") or source.get("objectName") or object_number)
    department = str(source.get("department") or "The Metropolitan Museum of Art")
    culture = str(source.get("culture") or "未标注")
    tags = _source_tags(source)
    filename = target_file.name
    source_url = str(source.get("objectURL") or f"https://www.metmuseum.org/art/collection/search/{object_id}")
    image_url = str(source.get("primaryImage") or source.get("primaryImageSmall") or "")

    business_metadata: dict[str, Any] = {
        "source_id": f"met:{object_id}",
        "source_system": "the_met_open_access",
        "source_label": "The Metropolitan Museum of Art Open Access",
        "title": _title(source),
        "resource_type": "image_2d_cultural_object",
        "visibility_scope": "open",
        "collection_object_id": object_id,
        "metadata_profile": "movable_artifact",
        "project_type": "开放博物馆真实数据测试集",
        "project_name": "MDAMS 二维真实数据测试集（The Met Open Access）",
        "photographer": "The Metropolitan Museum of Art",
        "photographer_org": "The Metropolitan Museum of Art",
        "capture_time": "源 API 未提供影像拍摄时间",
        "image_category": "可移动文物",
        "image_name": object_name,
        "capture_content": f"{department}藏品开放图像；年代：{source.get('objectDate') or '未标注'}；材质：{source.get('medium') or '未标注'}。",
        "representative_image": True,
        "remark": "真实公共领域藏品数据。完整官方 API 源记录保存在 raw_metadata.source_record。",
        "tags": ", ".join(tags),
        "record_account": "startup_demo_seed",
        "record_time": DATASET_TIMESTAMP,
        "image_record_time": DATASET_TIMESTAMP,
        "object_number": object_number,
        "object_name": object_name,
        "object_level": "参考品",
        "object_category": _object_category(source),
        "object_subcategory": str(source.get("objectName") or "其他"),
        "management_group": department,
        "visible_to_custodians_only": False,
        "original_file_name": filename,
        "image_file_name": filename,
        "iiif_access_file_name": filename,
        "iiif_access_file_path": str(target_file),
        "iiif_access_mime_type": "image/jpeg",
        "preview_image_name": filename,
        "preview_image_path": str(target_file),
        "preview_image_mime_type": "image/jpeg",
        "identifier_type": "The Met Object ID",
        "identifier_value": str(object_id),
        "file_size": target_file.stat().st_size,
        "format_name": "JPEG",
        "format_version": "JFIF/Exif",
        "registry_name": "IANA Media Types",
        "registry_item": "image/jpeg",
        "byte_order": "not applicable",
        "checksum_algorithm": "SHA256",
        "checksum": checksum,
        "checksum_generator": "MDAMS startup demo seed",
        "fixity_sha256": checksum,
        "fixity_status": "verified",
        "last_verified_at": datetime.now(timezone.utc).isoformat(),
        "width": width,
        "height": height,
        "color_space": "RGB",
        "ingest_method": "startup_demo_seed",
        "original_file_path": str(target_file),
        "original_file_size": target_file.stat().st_size,
        "original_mime_type": "image/jpeg",
        "copyright_status": "公共领域",
        "copyright_owner": "The Metropolitan Museum of Art",
        "access_scope": "公开",
        "allowed_usage": "不受限制的商业与非商业使用",
        "license": "CC0 1.0",
        "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        "allow_derivatives": True,
        "usage_restrictions": "无；使用时建议保留来源说明。",
        "rights_holder": "Public Domain / The Metropolitan Museum of Art Open Access",
        "permission_notes": "The Met Open Access 公共领域图像，可自由复制、修改与分发。",
        "source_url": source_url,
        "source_image_url": image_url,
        "object_date": source.get("objectDate"),
        "culture": culture,
        "period": source.get("period"),
        "dynasty": source.get("dynasty"),
        "reign": source.get("reign"),
        "medium": source.get("medium"),
        "dimensions": source.get("dimensions"),
        "credit_line": source.get("creditLine"),
        "repository": "The Metropolitan Museum of Art",
    }

    return build_metadata_layers(
        asset_filename=filename,
        asset_file_path=str(target_file),
        asset_file_size=target_file.stat().st_size,
        asset_mime_type="image/jpeg",
        asset_status="ready",
        asset_resource_type="image_2d_cultural_object",
        asset_visibility_scope="open",
        asset_collection_object_id=object_id,
        metadata=business_metadata,
        source_metadata={
            "dataset": "MDAMS 2D real-data test dataset",
            "dataset_version": "2026.07",
            "source_system": "the_met_open_access",
            "source_url": source_url,
            "source_image_url": image_url,
            "open_access_policy_url": OPEN_ACCESS_POLICY_URL,
            "retrieved_at": DATASET_TIMESTAMP,
            "source_record": source,
        },
        profile_hint="movable_artifact",
    )


def _get_or_create_sheet(db: Session) -> ImageIngestSheet:
    sheet = db.query(ImageIngestSheet).filter(ImageIngestSheet.sheet_no == DATASET_SHEET_NO).first()
    if sheet is None:
        sheet = ImageIngestSheet(sheet_no=DATASET_SHEET_NO)
        db.add(sheet)
        db.flush()
    sheet.title = "MDAMS 二维真实数据测试集（The Met Open Access，20 条）"
    sheet.status = "approved"
    sheet.image_type = "movable_artifact"
    sheet.project_type = "开放博物馆真实数据测试集"
    sheet.project_name = "MDAMS 二维真实数据测试集"
    sheet.photographer = "The Metropolitan Museum of Art"
    sheet.photographer_org = "The Metropolitan Museum of Art"
    sheet.copyright_owner = "Public Domain"
    sheet.capture_time = "源 API 未提供影像拍摄时间"
    sheet.remark = "20 条真实公共领域藏品数据；用于管理、预览、下载、完整性校验与统一检索测试。"
    sheet.metadata_info = {
        "dataset_key": "mdams-2d-met-open-access-20",
        "dataset_version": "2026.07",
        "record_count": len(DEMO_TWO_D_OBJECT_IDS),
        "source": "The Metropolitan Museum of Art Collection API",
        "license": "CC0 1.0",
        "open_access_policy_url": OPEN_ACCESS_POLICY_URL,
    }
    return sheet


def seed_demo_two_d_assets(db: Session) -> None:
    """Register 20 real, public-domain 2D museum records and their image files."""
    sheet = _get_or_create_sheet(db)
    target_dir = _target_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    for line_no, object_id in enumerate(DEMO_TWO_D_OBJECT_IDS, start=1):
        source = _load_source_record(object_id)
        source_file = _asset_source_dir() / f"met-{object_id}.jpg"
        if not source_file.exists():
            raise FileNotFoundError(f"Demo 2D source file not found: {source_file}")

        target_file = target_dir / source_file.name
        shutil.copy2(source_file, target_file)
        checksum = hashlib.sha256(target_file.read_bytes()).hexdigest()
        with Image.open(target_file) as image:
            width, height = image.size

        metadata_layers = _build_metadata(
            source=source,
            target_file=target_file,
            width=width,
            height=height,
            checksum=checksum,
        )
        record_no = f"MET-OA-{object_id}"
        record = db.query(ImageRecord).filter(ImageRecord.record_no == record_no).first()
        if record is None:
            record = ImageRecord(record_no=record_no)
            db.add(record)
            db.flush()
        record.sheet = sheet
        record.line_no = line_no
        record.title = _title(source)
        record.status = "approved"
        record.resource_type = "image_2d_cultural_object"
        record.visibility_scope = "open"
        record.collection_object_id = object_id
        record.profile_key = "movable_artifact"
        record.metadata_info = metadata_layers

        asset = db.query(Asset).filter(Asset.filename == source_file.name).first()
        if asset is None:
            asset = Asset(filename=source_file.name)
            db.add(asset)
            db.flush()
        asset.file_path = str(target_file)
        asset.file_size = target_file.stat().st_size
        asset.mime_type = "image/jpeg"
        asset.visibility_scope = "open"
        asset.collection_object_id = object_id
        asset.image_record = record
        asset.metadata_info = metadata_layers
        asset.resource_type = "image_2d_cultural_object"
        asset.status = "ready"
        asset.process_message = "服务启动时登记的 The Met Open Access 二维真实测试资源"

    db.commit()
