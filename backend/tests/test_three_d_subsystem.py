import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile

from app import config as app_config
from app.platform import three_d_source
from app.routers import platform as platform_router
from app.routers import three_d as three_d_router


pytestmark = [pytest.mark.system, pytest.mark.integration, pytest.mark.contract]


def _make_file_bytes(content: bytes):
    buffer = BytesIO()
    buffer.write(content)
    buffer.seek(0)
    return buffer


def _make_glb_bytes():
    return _make_file_bytes(b"glTF")


def _make_ply_bytes():
    return _make_file_bytes(b"ply")


def _make_jpg_bytes():
    return _make_file_bytes(b"\xff\xd8\xff\xe0JFIF")


async def _upload_three_d_sample(db_session, filename: str = "model.glb"):
    file = UploadFile(file=_make_glb_bytes(), filename=filename)
    return await three_d_router.upload_three_d_resource(
        file=file,
        title="古建三维模型",
        resource_group="古建A",
        version_label="original",
        version_order=0,
        is_current=True,
        is_web_preview=False,
        web_preview_status="disabled",
        web_preview_reason="原始版不对外展示",
        profile_key="model",
        project_name="3D 测试项目",
        creator="Codex",
        creator_org="MDAMS Lab",
        object_number="DEMO-3D-0001",
        object_name="古建三维模型",
        object_type="可移动文物",
        collection_unit="MDAMS Lab",
        object_summary="用于验证三维对象和藏品对象的强关联。",
        object_keywords="古建, 三维, 示例",
        format_name="glb",
        coordinate_system="local",
        unit="m",
        vertex_count=1024,
        face_count=2048,
        material_count=12,
        texture_count=8,
        point_count=None,
        lod_count=2,
        capture_time=None,
        db=db_session,
    )


async def _upload_three_d_package(db_session):
    model_files = [UploadFile(file=_make_glb_bytes(), filename="scene-model.glb")]
    point_cloud_files = [UploadFile(file=_make_ply_bytes(), filename="scene-point.ply")]
    oblique_files = [UploadFile(file=_make_jpg_bytes(), filename="scene-oblique-01.jpg")]
    return await three_d_router.upload_three_d_resource(
        mesh_uploads=model_files,
        point_cloud_uploads=point_cloud_files,
        oblique_uploads=oblique_files,
        title="倾斜摄影资源包",
        resource_group="三维资源组A",
        version_label="v1",
        version_order=1,
        is_current=True,
        is_web_preview=True,
        web_preview_status="ready",
        web_preview_reason=None,
        profile_key="package",
        project_name="3D 采集项目",
        creator="Codex",
        creator_org="MDAMS Lab",
        format_name="mixed",
        coordinate_system="local",
        unit="m",
        vertex_count=1234,
        face_count=4321,
        material_count=3,
        texture_count=6,
        point_count=998877,
        lod_count=1,
        capture_time="2026-03-27",
        db=db_session,
    )


async def _upload_three_d_linked_sample(db_session, collection_object_id: int):
    file = UploadFile(file=_make_glb_bytes(), filename="linked-model.glb")
    return await three_d_router.upload_three_d_resource(
        file=file,
        title="已关联三维模型",
        resource_group="鍏宠仈A",
        version_label="v2",
        version_order=2,
        is_current=False,
        is_web_preview=True,
        web_preview_status="ready",
        web_preview_reason=None,
        profile_key="model",
        project_name="3D 测试项目",
        creator="Codex",
        creator_org="MDAMS Lab",
        collection_object_id=collection_object_id,
        format_name="glb",
        coordinate_system="local",
        unit="m",
        vertex_count=2048,
        face_count=4096,
        material_count=8,
        texture_count=4,
        point_count=None,
        lod_count=1,
        capture_time=None,
        db=db_session,
    )


def test_three_d_resource_subsystem_and_platform_adapter(db_session, test_upload_dir, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))

    uploaded = asyncio.run(_upload_three_d_sample(db_session))

    resources = three_d_router.list_three_d_resources(db=db_session)
    assert len(resources) == 1
    resource = resources[0]
    assert resource.id == uploaded.id
    assert resource.profile_key == "model"
    assert resource.profile_label == "三维模型"
    assert resource.title == "古建三维模型"
    assert resource.file_count == 1
    assert resource.primary_file_role == "model"
    assert resource.version_label == "original"
    assert resource.web_preview_status == "disabled"

    detail = three_d_router.get_three_d_resource(resource_id=resource.id, db=db_session)
    assert detail.id == uploaded.id
    assert detail.profile_key == "model"
    assert detail.profile_label == "三维模型"
    assert detail.version_label == "original"
    assert detail.web_preview_status == "disabled"
    assert detail.metadata_layers["core"]["profile_key"] == "model"
    assert detail.outputs.download_url.endswith(f"/api/three-d/resources/{uploaded.id}/download")
    assert detail.viewer is not None
    assert detail.viewer.enabled is False
    assert detail.viewer.preview_file is not None
    assert detail.viewer.preview_file.role == "model"
    assert detail.structure.primary_file.role == "model"
    assert len(detail.structure.files) == 1

    viewer_summary = three_d_router.get_three_d_resource_viewer(resource_id=resource.id, db=db_session)
    assert viewer_summary.enabled is False
    assert viewer_summary.preview_file is not None
    assert viewer_summary.preview_file.role == "model"

    sources = platform_router.get_sources(db=db_session)
    assert any(source.source_system == three_d_source.SOURCE_SYSTEM for source in sources)
    three_d_summary = next(source for source in sources if source.source_system == three_d_source.SOURCE_SYSTEM)
    assert three_d_summary.resource_count == 1
    assert three_d_summary.entrypoint == "/api/three-d/resources"

    unified_resources = platform_router.get_resources(source_system=three_d_source.SOURCE_SYSTEM, db=db_session)
    assert len(unified_resources) == 1
    unified_resource = unified_resources[0]
    assert unified_resource.id == f"{three_d_source.SOURCE_SYSTEM}:{uploaded.id}"
    assert unified_resource.profile_key == "model"
    assert unified_resource.profile_label == "三维模型"
    assert unified_resource.preview_enabled is False
    assert unified_resource.detail_url == f"/api/platform/resources/{unified_resource.source_system}/{unified_resource.source_id}"
    assert {action.key for action in unified_resource.actions} == {
        "preview",
        "platform_detail",
        "source_detail",
        "download",
    }
    preview_action = next(action for action in unified_resource.actions if action.key == "preview")
    assert preview_action.enabled is False
    assert preview_action.target == "access_representation"

    unified_detail = platform_router.get_resource(source_system=unified_resource.source_system, source_id=unified_resource.source_id, db=db_session)
    assert unified_detail.id == unified_resource.id
    assert unified_detail.source_system == three_d_source.SOURCE_SYSTEM
    assert unified_detail.detail_url == f"/api/platform/resources/{unified_resource.source_system}/{unified_resource.source_id}"
    assert unified_detail.source_detail_url == f"/api/three-d/resources/{uploaded.id}"
    assert unified_detail.source_record_type == "three_d_detail"
    assert unified_detail.source_record_schema == "three_d_detail.v1"
    assert unified_detail.source_record is not None
    assert unified_detail.source_record["id"] == uploaded.id
    assert unified_detail.source_record["structure"]["primary_file"]["role"] == "model"
    assert unified_detail.source_record["production_records"] == []
    assert next(action for action in unified_detail.actions if action.key == "download").target == "source"

    collection_objects = three_d_router.list_three_d_collection_objects(q="古建", db=db_session)
    assert len(collection_objects) == 1
    assert collection_objects[0].id == detail.collection_object.id

    linked = asyncio.run(_upload_three_d_linked_sample(db_session, detail.collection_object.id))
    linked_detail = three_d_router.get_three_d_resource(resource_id=linked.id, db=db_session)
    assert linked_detail.collection_object is not None
    assert linked_detail.collection_object.id == detail.collection_object.id
    assert linked_detail.collection_object.object_number == detail.collection_object.object_number
    assert linked_detail.collection_object.object_name == detail.collection_object.object_name


def test_three_d_package_resource_stores_multiple_file_roles(db_session, test_upload_dir, monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(test_upload_dir))

    uploaded = asyncio.run(_upload_three_d_package(db_session))
    package_dir = Path(test_upload_dir) / "three-d" / str(uploaded.id)
    assert package_dir.exists()

    detail = three_d_router.get_three_d_resource(resource_id=uploaded.id, db=db_session)
    assert detail.profile_key == "package"
    assert detail.resource_type == "three_d_package"
    assert detail.version_label == "v1"
    assert detail.is_web_preview is True
    assert detail.access.preview_enabled is True
    assert detail.viewer is not None
    assert detail.viewer.enabled is True
    assert detail.viewer.preview_file is not None
    assert detail.viewer.preview_file.role == "model"
    assert detail.viewer.preview_url is not None
    assert detail.structure.packaging is not None
    assert detail.structure.packaging.file_count == 3
    assert len(detail.structure.files) == 3
    assert {item.role for item in detail.structure.files} == {"model", "point_cloud", "oblique_photo"}
    assert detail.file.file_size > 0
    oblique_file = next(item for item in detail.structure.files if item.role == "oblique_photo")
    assert oblique_file.preview_url is not None
    assert oblique_file.download_url is not None

    viewer_summary = three_d_router.get_three_d_resource_viewer(resource_id=uploaded.id, db=db_session)
    assert viewer_summary.enabled is True
    assert viewer_summary.preview_file is not None
    assert viewer_summary.preview_file.role == "model"
    assert viewer_summary.preview_url is not None

    preview_response = three_d_router.download_three_d_resource_file(
        resource_id=uploaded.id,
        file_id=oblique_file.id or 0,
        db=db_session,
    )
    assert Path(preview_response.path).exists()

    download_response = three_d_router.download_three_d_resource(resource_id=uploaded.id, db=db_session)
    assert download_response.media_type == "application/zip"
    assert Path(download_response.path).exists()

    unified_resources = platform_router.get_resources(source_system=three_d_source.SOURCE_SYSTEM, db=db_session)
    assert len(unified_resources) == 1
    assert unified_resources[0].profile_key == "package"
    assert unified_resources[0].resource_type == "three_d_package"
    assert unified_resources[0].preview_enabled is True
    assert next(action for action in unified_resources[0].actions if action.key == "preview").enabled is True
