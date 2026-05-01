from pathlib import Path

import pytest
from PIL import Image

from app.services.reference_import import (
    assess_manifest_completeness,
    build_import_filename,
    build_reference_manifest,
    collect_reference_candidates,
    select_primary_image,
)


pytestmark = [pytest.mark.unit, pytest.mark.contract]


def _write_image(path: Path, size=(16, 16), color="white"):
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, color=color)
    image.save(path)


def test_select_primary_image_prefers_non_screenshot(tmp_path):
    folder = tmp_path / "resource"
    _write_image(folder / "FireShot Capture 001.jpg", color="red")
    _write_image(folder / "artifact.jpg", color="blue")

    selected = select_primary_image(folder)

    assert selected is not None
    assert selected.name == "artifact.jpg"


def test_build_reference_manifest_maps_external_profile_aliases(tmp_path):
    source_root = tmp_path / "reference"
    resource_dir = source_root / "文物建筑影像" / "长春宫内景"
    _write_image(resource_dir / "CCG0008_PMIM_41392494_1023032218.tif")
    _write_image(resource_dir / "FireShot Capture 476.jpg")
    (resource_dir / "FireShot Capture 476.unified.json").write_text(
        """
        {
          "source_id": "abc-123",
          "source_label": "文物建筑影像",
          "profile_key": "building",
          "title": "长春宫内景",
          "summary": "建筑影像样本",
          "keywords": ["建筑", "内景"],
          "rights": "故宫博物院",
          "updated_at": "2026-03-31T10:00:00",
          "metadata_layers": {
            "core": {
              "capture_date": "2026-03-30",
              "recorded_at": "2026-03-31T10:00:00"
            },
            "technical": {
              "source_image_file": "CCG0008_PMIM_41392494_1023032218.tif"
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    candidate = build_reference_manifest(
        source_dir=resource_dir,
        source_root=source_root,
    )

    assert candidate is not None
    assert candidate.profile_key == "immovable_artifact"
    assert candidate.primary_image.name == "CCG0008_PMIM_41392494_1023032218.tif"
    assert candidate.manifest["metadata"]["profile"]["key"] == "immovable_artifact"
    assert candidate.manifest["metadata"]["profile"]["fields"]["building_name"] == "长春宫内景"
    assert candidate.manifest["metadata"]["management"]["image_name"] == "长春宫内景"


def test_collect_reference_candidates_skips_dirs_without_images(tmp_path):
    source_root = tmp_path / "reference"
    empty_dir = source_root / "其他影像" / "资料"
    empty_dir.mkdir(parents=True)
    resource_dir = source_root / "考古影像" / "响堂山"
    _write_image(resource_dir / "img0028.jpg")

    candidates = collect_reference_candidates(source_root)

    assert len(candidates) == 1
    assert candidates[0].source_dir == resource_dir


def test_build_import_filename_is_stable_and_unique_per_relative_dir(tmp_path):
    image = tmp_path / "sample.jpg"
    _write_image(image)

    first = build_import_filename(image, Path("文物影像/目录A"))
    second = build_import_filename(image, Path("文物影像/目录B"))

    assert first.endswith(".jpg")
    assert second.endswith(".jpg")
    assert first != second


def test_assess_manifest_completeness_reports_missing_profile_fields():
    manifest = {
        "hash": "abc",
        "metadata": {
            "core": {
                "title": "测试资源",
                "source_system": "reference_resource_pack",
                "resource_type": "image_2d_cultural_object",
                "visibility_scope": "open",
            },
            "management": {
                "project_name": "测试目录",
                "image_category": "文物影像",
                "image_name": "测试资源",
            },
            "technical": {
                "original_file_name": "sample.jpg",
                "file_size": 1024,
                "checksum": "abc",
                "ingest_method": "reference_manifest",
            },
            "profile": {
                "key": "business_activity",
                "fields": {},
            },
        },
    }

    result = assess_manifest_completeness(manifest)

    assert result["profile_key"] == "business_activity"
    assert "profile.main_location" in result["missing"]
    assert result["filled"] == 11
    assert result["expected"] == 12


def test_assess_manifest_completeness_uses_shared_movable_artifact_rules():
    manifest = {
        "hash": "abc",
        "metadata": {
            "core": {
                "title": "铜镜正面",
                "source_system": "reference_resource_pack",
                "resource_type": "image_2d_cultural_object",
                "visibility_scope": "open",
            },
            "management": {
                "project_name": "文物影像",
                "image_category": "文物影像",
                "image_name": "铜镜正面",
            },
            "technical": {
                "original_file_name": "artifact.jpg",
                "file_size": 1024,
                "checksum": "abc",
                "ingest_method": "reference_manifest",
            },
            "profile": {
                "key": "movable_artifact",
                "fields": {
                    "object_name": "铜镜",
                },
            },
        },
    }

    result = assess_manifest_completeness(manifest)

    assert result["profile_key"] == "movable_artifact"
    assert "profile.object_number" in result["missing"]
    assert result["filled"] == 11
    assert result["expected"] == 12


def test_build_reference_manifest_extracts_business_activity_location_and_person(tmp_path):
    source_root = tmp_path / "reference"
    resource_dir = source_root / "业务活动影像" / "标准化工作会议"
    _write_image(resource_dir / "meeting.jpg")
    (resource_dir / "FireShot Capture 001.unified.json").write_text(
        """
        {
          "source_id": "abc-456",
          "source_label": "业务活动影像",
          "profile_key": "activity",
          "title": "标准化工作会议",
          "metadata_layers": {
            "modality": {
              "主题地点": "致正斋",
              "主要人物": "王旭东"
            },
            "source_record": {
              "主题地点": "致正斋",
              "主要人物": "王旭东"
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    candidate = build_reference_manifest(source_dir=resource_dir, source_root=source_root)

    assert candidate is not None
    assert candidate.manifest["metadata"]["profile"]["fields"]["main_location"] == "致正斋"
    assert candidate.manifest["metadata"]["profile"]["fields"]["main_person"] == "王旭东"


def test_build_reference_manifest_extracts_movable_artifact_object_number_when_present(tmp_path):
    source_root = tmp_path / "reference"
    resource_dir = source_root / "文物影像" / "铜镜正面"
    _write_image(resource_dir / "artifact.tif")
    (resource_dir / "artifact.unified.json").write_text(
        """
        {
          "source_id": "artifact-123",
          "source_label": "文物影像",
          "profile_key": "movable_artifact",
          "title": "铜镜正面",
          "metadata_layers": {
            "source_record": {
              "文物号": "故00123456"
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    candidate = build_reference_manifest(source_dir=resource_dir, source_root=source_root)

    assert candidate is not None
    assert candidate.manifest["metadata"]["profile"]["fields"]["object_name"] == "铜镜正面"
    assert candidate.manifest["metadata"]["profile"]["fields"]["object_number"] == "故00123456"

    completeness = assess_manifest_completeness(candidate.manifest)
    assert completeness["missing"] == []
    assert completeness["ratio"] == 1.0
