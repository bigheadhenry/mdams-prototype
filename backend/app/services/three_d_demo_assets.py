from __future__ import annotations

import shutil
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .. import config
from ..models import ThreeDAsset, ThreeDAssetFile, ThreeDCollectionObject, ThreeDProductionRecord
from .three_d_metadata import build_three_d_metadata_layers
from .three_d_objects import get_or_create_digital_object, infer_representation_type, normalize_publication_status
from .fixity import calculate_sha256
from .three_d_preview import build_three_d_preview_data
from .three_d_production import seed_three_d_production_records
from .three_d_storage import build_three_d_package_manifest, three_d_role_label


@dataclass(frozen=True)
class DemoThreeDFile:
    filename: str
    role: str = "model"
    actual_filename: str | None = None
    is_primary: bool = False


@dataclass(frozen=True)
class DemoThreeDAsset:
    resource_group: str
    title: str
    object_number: str
    object_name: str
    files: tuple[DemoThreeDFile, ...]
    version_label: str = "preview"
    version_order: int = 1
    is_current: bool = True
    is_web_preview: bool = True
    web_preview_status: str = "ready"
    web_preview_reason: str | None = None
    resource_type: str = "three_d_model"
    profile_key: str = "model"
    source_url: str = ""
    license_label: str = "Demo"
    credit: str = "MDAMS Demo Collection"
    vertex_count: int | None = None
    face_count: int | None = None
    point_count: int | None = None
    material_count: int | None = 1
    texture_count: int | None = 0
    lod_count: int | None = 1
    coordinate_system: str = "local"
    unit: str = "m"
    object_type: str = "标准测试模型"
    collection_unit: str = "MDAMS Demo Collection"
    object_summary: str = "服务启动时登记的三维预览样本，用于验证资源目录和 Web 预览链路。"
    object_keywords: str = ""
    creator_org: str = "MDAMS Demo Collection"
    project_name: str = "MDAMS startup 3D preview samples"
    creator: str | None = None
    capture_time: str | None = None
    storage_tier: str = "archive"
    preservation_status: str = "preserved"
    preservation_note: str | None = None
    extra_metadata: dict[str, Any] = field(default_factory=dict)


DEMO_THREE_D_ASSETS = (
    DemoThreeDAsset(
        resource_group="demo-khronos-box",
        title="Khronos Box 线上样本",
        object_number="DEMO-3D-KHRONOS-BOX",
        object_name="Khronos Box",
        files=(DemoThreeDFile("khronos-box.gltf", is_primary=True),),
        source_url="https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Box",
        license_label="CC BY 4.0",
        credit="Cesium",
        vertex_count=24,
        face_count=12,
        unit="unit",
    ),
    DemoThreeDAsset(
        resource_group="demo-khronos-triangle",
        title="Khronos Triangle 线上样本",
        object_number="DEMO-3D-KHRONOS-TRIANGLE",
        object_name="Khronos Triangle",
        files=(DemoThreeDFile("khronos-triangle.gltf", is_primary=True),),
        source_url="https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Triangle",
        license_label="CC0 1.0",
        credit="Marco Hutter",
        vertex_count=3,
        face_count=1,
        unit="unit",
    ),
    DemoThreeDAsset(
        resource_group="demo-sketchfab-british-museum-horus",
        title="Horus",
        object_number="DEMO-3D-BM-HORUS",
        object_name="Horus",
        files=(DemoThreeDFile("horus.glb", is_primary=True),),
        source_url="https://sketchfab.com/3d-models/horus-e62f9907d04041e7bcd485e51063b8d5",
        license_label="CC BY-NC-SA",
        credit="The British Museum",
        vertex_count=90300,
        face_count=180600,
        object_type="Sketchfab 三维藏品模型",
        collection_unit="The British Museum",
        object_summary="来自 Sketchfab 的 Horus 三维模型样本，用于验证 GLB 文件上传、元数据登记和 Web 预览链路。",
        object_keywords="Horus, The British Museum, Sketchfab, GLB, Egyptian, 3D model, CC BY-NC-SA",
        creator_org="The British Museum",
        project_name="Sketchfab downloadable 3D model preview test",
        material_count=1,
        texture_count=1,
    ),
    DemoThreeDAsset(
        resource_group="demo-museum-vase-object",
        title="博物馆陶罐三维对象 - 原始采集包",
        object_number="DEMO-3D-VASE-0001",
        object_name="陶罐三维数字对象",
        files=(
            DemoThreeDFile("museum-vase-source.gltf", role="model", is_primary=True),
            DemoThreeDFile("museum-vase-source.bin", role="support"),
            DemoThreeDFile("museum-vase-texture.png", role="texture"),
            DemoThreeDFile("museum-vase-point-cloud.pts", role="point_cloud"),
            DemoThreeDFile("museum-vase-capture-report.txt", role="support"),
        ),
        version_label="original",
        version_order=0,
        is_current=False,
        is_web_preview=False,
        web_preview_status="disabled",
        web_preview_reason="原始采集包保留完整依赖文件，不作为 Web 发布版本。",
        resource_type="three_d_package",
        profile_key="package",
        source_url="bundled://demo/museum-vase-source",
        license_label="Synthetic demo asset",
        credit="MDAMS Demo 3D Lab",
        vertex_count=642,
        face_count=1280,
        point_count=10,
        material_count=1,
        texture_count=1,
        lod_count=1,
        object_type="陶瓷器",
        collection_unit="MDAMS Demo Collection",
        object_summary="用于测试完整对象元数据、多文件资源包、采集包与发布包分离的陶罐三维对象。",
        object_keywords="陶罐, glTF, 点云, 纹理, 采集报告, 资源包",
        creator_org="MDAMS 3D Lab",
        project_name="三维对象完整资源包演示",
        creator="MDAMS 3D Lab",
        capture_time="2026-05-16",
        preservation_note="原始采集包保存 glTF、BIN、贴图、点云和采集报告，用于长期保存验证。",
        extra_metadata={
            "capture_batch": "3D-DEMO-2026-001",
            "capture_method": "structured_light_scan_with_reference_photos",
            "quality_grade": "demo-complete",
        },
    ),
    DemoThreeDAsset(
        resource_group="demo-museum-vase-object",
        title="博物馆陶罐三维对象 - Web 发布版",
        object_number="DEMO-3D-VASE-0001",
        object_name="陶罐三维数字对象",
        files=(
            DemoThreeDFile("museum-vase-preview.glb", role="model", is_primary=True),
            DemoThreeDFile("museum-vase-texture.png", role="texture"),
            DemoThreeDFile("museum-vase-capture-report.txt", role="support"),
        ),
        version_label="v1-web",
        version_order=1,
        is_current=True,
        is_web_preview=True,
        web_preview_status="ready",
        web_preview_reason="轻量化 GLB 已登记为 Web 展示版本。",
        resource_type="three_d_package",
        profile_key="package",
        source_url="bundled://demo/museum-vase-preview",
        license_label="Synthetic demo asset",
        credit="MDAMS Demo 3D Lab",
        vertex_count=642,
        face_count=1280,
        material_count=1,
        texture_count=1,
        lod_count=2,
        object_type="陶瓷器",
        collection_unit="MDAMS Demo Collection",
        object_summary="同一陶罐对象的 Web 发布版本，用于测试对象聚合、版本展开和在线三维预览。",
        object_keywords="陶罐, GLB, Web 展示, 轻量化发布版",
        creator_org="MDAMS 3D Lab",
        project_name="三维对象完整资源包演示",
        creator="MDAMS 3D Lab",
        capture_time="2026-05-16",
        storage_tier="delivery",
        preservation_status="preserved",
        preservation_note="发布版与原始采集包分层保存，便于展示和长期保存分离。",
        extra_metadata={
            "publish_batch": "3D-PUB-2026-001",
            "derived_from": "original",
            "quality_grade": "web-ready",
        },
    ),
    DemoThreeDAsset(
        resource_group="demo-museum-vase-object",
        title="博物馆陶罐三维对象 - 高精度处理版",
        object_number="DEMO-3D-VASE-0001",
        object_name="陶罐三维数字对象",
        files=(
            DemoThreeDFile("museum-vase-detail.glb", role="model", is_primary=True),
            DemoThreeDFile("museum-vase-point-cloud.pts", role="point_cloud"),
            DemoThreeDFile("museum-vase-capture-report.txt", role="support"),
        ),
        version_label="v2-detail",
        version_order=2,
        is_current=False,
        is_web_preview=True,
        web_preview_status="ready",
        web_preview_reason="高精度 GLB 可用于对比浏览，但当前业务展示版仍为 v1-web。",
        resource_type="three_d_package",
        profile_key="package",
        source_url="bundled://demo/museum-vase-detail",
        license_label="Synthetic demo asset",
        credit="MDAMS Demo 3D Lab",
        vertex_count=1920,
        face_count=3840,
        point_count=10,
        material_count=1,
        texture_count=1,
        lod_count=3,
        object_type="陶瓷器",
        collection_unit="MDAMS Demo Collection",
        object_summary="同一陶罐对象的高精度处理版本，用于测试多版本对象治理和文件构成展示。",
        object_keywords="陶罐, GLB, 高精度, 点云, 处理版",
        creator_org="MDAMS 3D Lab",
        project_name="三维对象完整资源包演示",
        creator="MDAMS 3D Lab",
        capture_time="2026-05-16",
        storage_tier="archive",
        preservation_status="preserved",
        preservation_note="高精度处理版保留为归档层版本，也可用于浏览对比。",
        extra_metadata={
            "processing_batch": "3D-PROC-2026-001",
            "derived_from": "original",
            "quality_grade": "detail",
        },
    ),
    DemoThreeDAsset(
        resource_group="demo-ancient-building-scene",
        title="古建场景三维资源包 - 综合演示对象",
        object_number="DEMO-3D-BUILDING-0001",
        object_name="古建场景三维数字对象",
        files=(
            DemoThreeDFile("pyramid.gltf", role="model", is_primary=True),
            DemoThreeDFile("ancient-building-point-cloud.pts", role="point_cloud"),
            DemoThreeDFile("museum-vase-texture.png", role="oblique_photo", actual_filename="ancient-building-oblique-reference.png"),
            DemoThreeDFile("ancient-building-production-note.txt", role="support"),
        ),
        version_label="v1-integrated",
        version_order=1,
        is_current=True,
        is_web_preview=True,
        web_preview_status="ready",
        web_preview_reason="综合资源包中的 glTF 主模型可用于 Web 预览，其余文件用于验证资源包构成。",
        resource_type="three_d_package",
        profile_key="package",
        source_url="bundled://demo/ancient-building-scene",
        license_label="Synthetic demo asset",
        credit="MDAMS Demo 3D Lab",
        vertex_count=96,
        face_count=64,
        point_count=10,
        material_count=1,
        texture_count=1,
        lod_count=1,
        object_type="不可移动文物",
        collection_unit="MDAMS Demo Collection",
        object_summary="包含模型、点云、倾斜摄影参考图和生产说明的古建场景资源包，用于测试多文件角色与统一详情展示。",
        object_keywords="古建, 场景, glTF, 点云, 倾斜摄影, 生产说明",
        creator_org="MDAMS 3D Lab",
        project_name="三维场景资源包演示",
        creator="MDAMS 3D Lab",
        capture_time="2026-05-16",
        preservation_note="综合演示对象用于验证多文件资源包、Web 预览和保存层字段。",
        extra_metadata={
            "capture_batch": "3D-DEMO-2026-002",
            "processing_pipeline": "alignment -> reconstruction -> simplification -> web_publish",
            "quality_grade": "demo-package",
        },
    ),
)


def _asset_source_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "demo_assets" / "three_d"


def _resource_dir(asset_id: int) -> Path:
    return Path(config.UPLOAD_DIR) / "three-d" / str(asset_id)


def _mime_type_for_filename(filename: str) -> str:
    name = filename.lower()
    if name.endswith(".glb"):
        return "model/gltf-binary"
    if name.endswith(".gltf"):
        return "model/gltf+json"
    if name.endswith(".png"):
        return "image/png"
    if name.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if name.endswith((".pts", ".xyz")):
        return "text/plain"
    if name.endswith(".txt"):
        return "text/plain"
    if name.endswith(".bin"):
        return "application/octet-stream"
    return "application/octet-stream"


def _format_name_for_filename(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"


def _get_or_create_collection_object(db: Session, sample: DemoThreeDAsset) -> ThreeDCollectionObject:
    collection_object = (
        db.query(ThreeDCollectionObject)
        .filter(ThreeDCollectionObject.object_number == sample.object_number)
        .first()
    )
    if collection_object is None:
        collection_object = ThreeDCollectionObject(object_number=sample.object_number)
        db.add(collection_object)
        db.flush()

    collection_object.object_name = sample.object_name
    collection_object.object_type = sample.object_type
    collection_object.collection_unit = sample.collection_unit
    collection_object.summary = sample.object_summary
    collection_object.keywords = sample.object_keywords or f"3D, demo, {sample.license_label}"
    collection_object.metadata_info = {
        "object_number": sample.object_number,
        "object_name": sample.object_name,
        "object_type": collection_object.object_type,
        "collection_unit": collection_object.collection_unit,
        "summary": collection_object.summary,
        "keywords": collection_object.keywords,
        "demo_seed": True,
    }
    db.flush()
    return collection_object


def _copy_demo_files(asset: ThreeDAsset, sample: DemoThreeDAsset) -> list[dict[str, object]]:
    saved_files: list[dict[str, object]] = []
    primary_seen = False
    for sort_order, file_def in enumerate(sample.files):
        source_file = _asset_source_dir() / file_def.filename
        if not source_file.exists():
            raise FileNotFoundError(f"Demo 3D source file not found: {source_file}")

        role_dir = _resource_dir(asset.id) / "files" / file_def.role
        role_dir.mkdir(parents=True, exist_ok=True)
        actual_filename = file_def.actual_filename or source_file.name
        target_file = role_dir / actual_filename
        shutil.copyfile(source_file, target_file)

        is_primary = file_def.is_primary or (not primary_seen and file_def.role == "model")
        primary_seen = primary_seen or is_primary
        saved_files.append(
            {
                "role": file_def.role,
                "role_label": three_d_role_label(file_def.role),
                "filename": file_def.filename,
                "actual_filename": actual_filename,
                "file_path": str(target_file),
                "file_size": target_file.stat().st_size,
                "mime_type": _mime_type_for_filename(actual_filename),
                "sort_order": sort_order,
                "is_primary": is_primary,
            }
        )
    return saved_files


def _metadata_for_sample(
    asset: ThreeDAsset,
    sample: DemoThreeDAsset,
    file_records: list[dict[str, object]],
    preview_data: dict[str, Any],
) -> dict[str, Any]:
    primary_file = next((record for record in file_records if record.get("is_primary")), file_records[0])
    total_file_size = sum(int(record.get("file_size") or 0) for record in file_records)
    preservation_note = sample.preservation_note or f"Online sample source: {sample.source_url}; license: {sample.license_label}."
    metadata = {
        "title": sample.title,
        "three_d_profile": sample.profile_key,
        "resource_group": sample.resource_group,
        "three_d_object_id": asset.three_d_object_id,
        "representation_type": asset.representation_type,
        "publication_status": asset.publication_status,
        "version_label": sample.version_label,
        "version_order": sample.version_order,
        "is_current": sample.is_current,
        "is_web_preview": sample.is_web_preview,
        "web_preview_status": sample.web_preview_status,
        "web_preview_reason": sample.web_preview_reason or f"{sample.title} demo model registered for startup preview.",
        "project_name": sample.project_name,
        "creator": sample.creator or sample.credit,
        "creator_org": sample.creator_org,
        "object_number": sample.object_number,
        "object_name": sample.object_name,
        "object_type": sample.object_type,
        "collection_unit": sample.collection_unit,
        "object_summary": sample.object_summary,
        "object_keywords": sample.object_keywords or f"3D, demo, {sample.license_label}",
        "format_name": _format_name_for_filename(str(primary_file["actual_filename"])),
        "format_version": "2.0",
        "vertex_count": sample.vertex_count,
        "face_count": sample.face_count,
        "point_count": sample.point_count,
        "material_count": sample.material_count,
        "texture_count": sample.texture_count,
        "lod_count": sample.lod_count,
        "coordinate_system": sample.coordinate_system,
        "unit": sample.unit,
        "capture_time": sample.capture_time,
        "storage_tier": sample.storage_tier,
        "preservation_status": sample.preservation_status,
        "preservation_note": preservation_note,
        "ingest_method": "startup_demo_seed",
        "file_name": primary_file["actual_filename"],
        "file_size": total_file_size,
        "preview_data": preview_data,
        **sample.extra_metadata,
    }
    return build_three_d_metadata_layers(
        asset_id=asset.id,
        asset_filename=str(primary_file["actual_filename"]),
        asset_file_path=str(primary_file["file_path"]),
        asset_file_size=total_file_size,
        asset_mime_type=str(primary_file["mime_type"]),
        asset_status="ready",
        asset_resource_type=sample.resource_type,
        asset_created_at=asset.created_at,
        metadata=metadata,
        source_metadata={
            "source_url": sample.source_url,
            "license": sample.license_label,
            "credit": sample.credit,
            "files": file_records,
            "preview_data": preview_data,
            "profile_key": sample.profile_key,
            **sample.extra_metadata,
        },
        profile_hint=sample.profile_key,
        file_records=file_records,
    )


def seed_demo_three_d_assets(db: Session) -> None:
    """Register bundled previewable and package-style 3D samples."""
    for sample in DEMO_THREE_D_ASSETS:
        collection_object = _get_or_create_collection_object(db, sample)
        representation_type = infer_representation_type(
            version_label=sample.version_label,
            is_web_preview=sample.is_web_preview,
            web_preview_status=sample.web_preview_status,
        )
        publication_status = normalize_publication_status(
            None,
            preview_ready=bool(sample.is_web_preview and sample.web_preview_status == "ready"),
        )
        digital_object = get_or_create_digital_object(
            db,
            collection_object=collection_object,
            resource_group=sample.resource_group,
            title=sample.object_name or sample.title,
            responsible_department=sample.collection_unit,
        )
        asset = (
            db.query(ThreeDAsset)
            .filter(
                ThreeDAsset.resource_group == sample.resource_group,
                ThreeDAsset.version_label == sample.version_label,
            )
            .first()
        )
        if asset is None:
            asset = ThreeDAsset(
                three_d_object=digital_object,
                collection_object=collection_object,
                resource_group=sample.resource_group,
                filename=sample.files[0].actual_filename or sample.files[0].filename,
                file_path="",
                file_size=0,
                mime_type=_mime_type_for_filename(sample.files[0].actual_filename or sample.files[0].filename),
                status="ready",
                resource_type=sample.resource_type,
                version_label=sample.version_label,
                representation_type=representation_type,
                publication_status=publication_status,
                version_order=sample.version_order,
                is_current=sample.is_current,
                is_web_preview=sample.is_web_preview,
                web_preview_status=sample.web_preview_status,
                web_preview_reason=sample.web_preview_reason,
                storage_tier=sample.storage_tier,
                preservation_status=sample.preservation_status,
                preservation_note=sample.preservation_note,
                process_message="服务启动时登记的三维演示资源",
                metadata_info={},
            )
            db.add(asset)
            db.flush()
        else:
            asset.three_d_object = digital_object
            asset.collection_object = collection_object

        file_records = _copy_demo_files(asset, sample)
        resource_dir = _resource_dir(asset.id)
        preview_data = build_three_d_preview_data(
            resource_dir,
            asset_id=asset.id,
            title=sample.title,
            file_records=file_records,
        )
        metadata_layers = _metadata_for_sample(asset, sample, file_records, preview_data)
        manifest_path = build_three_d_package_manifest(
            resource_dir,
            asset=asset,
            metadata_layers=metadata_layers,
            file_records=file_records,
        )
        primary_file = next((record for record in file_records if record.get("is_primary")), file_records[0])
        total_file_size = sum(int(record.get("file_size") or 0) for record in file_records)

        asset.filename = str(primary_file["actual_filename"])
        asset.file_path = str(manifest_path if len(file_records) > 1 else primary_file["file_path"])
        asset.file_size = total_file_size
        asset.mime_type = "application/json" if len(file_records) > 1 else str(primary_file["mime_type"])
        asset.status = "ready"
        asset.resource_type = sample.resource_type
        asset.process_message = "服务启动时登记的三维演示资源"
        asset.version_label = sample.version_label
        asset.representation_type = representation_type
        asset.publication_status = publication_status
        asset.version_order = sample.version_order
        asset.is_current = sample.is_current
        asset.is_web_preview = sample.is_web_preview
        asset.web_preview_status = sample.web_preview_status
        asset.web_preview_reason = sample.web_preview_reason or f"{sample.title} demo model registered for startup preview."
        asset.storage_tier = sample.storage_tier
        asset.preservation_status = sample.preservation_status
        asset.preservation_note = sample.preservation_note or f"Online sample source: {sample.source_url}; license: {sample.license_label}."
        asset.metadata_info = metadata_layers

        db.query(ThreeDAssetFile).filter(ThreeDAssetFile.asset_id == asset.id).delete()
        for file_record in file_records:
            db.add(
                ThreeDAssetFile(
                    asset_id=asset.id,
                    role=str(file_record["role"]),
                    role_label=str(file_record["role_label"]),
                    filename=str(file_record["filename"]),
                    actual_filename=str(file_record["actual_filename"]),
                    file_path=str(file_record["file_path"]),
                    file_size=int(file_record["file_size"]),
                    mime_type=str(file_record["mime_type"]),
                    sort_order=int(file_record["sort_order"]),
                    is_primary=bool(file_record["is_primary"]),
                    sha256=calculate_sha256(str(file_record["file_path"])),
                    fixity_status="verified",
                    last_verified_at=datetime.now(timezone.utc),
                )
            )

        db.query(ThreeDProductionRecord).filter(ThreeDProductionRecord.asset_id == asset.id).delete()
        seed_three_d_production_records(
            db,
            asset,
            saved_files=file_records,
            manifest_path=str(manifest_path),
            preview_ready=bool(asset.is_web_preview and asset.web_preview_status == "ready"),
            preservation_status=sample.preservation_status,
            storage_tier=sample.storage_tier,
        )

    db.commit()
