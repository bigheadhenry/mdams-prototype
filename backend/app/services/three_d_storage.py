from __future__ import annotations

import json
import shutil
import uuid
import zipfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from fastapi import UploadFile


THREE_D_FILE_ROLE_LABELS = {
    "model": "三维模型",
    "point_cloud": "点云",
    "oblique_photo": "倾斜摄影图像",
    "texture": "贴图",
    "support": "辅助文件",
    "other": "其他",
}

THREE_D_FILE_ROLE_ORDER = ("model", "point_cloud", "oblique_photo", "texture", "support", "other")


def normalize_three_d_role(role: str | None) -> str:
    if not role:
        return "other"
    normalized = role.strip().lower()
    if normalized in {"model", "mesh", "glb", "gltf", "obj", "fbx", "stl", "usdz"}:
        return "model"
    if normalized in {"point_cloud", "pointcloud", "ply", "las", "laz", "xyz", "pts"}:
        return "point_cloud"
    if normalized in {"oblique", "oblique_photo", "oblique_photography", "scene", "photo", "images"}:
        return "oblique_photo"
    if normalized in {"texture", "textures"}:
        return "texture"
    if normalized in {"support", "aux", "auxiliary"}:
        return "support"
    if normalized in THREE_D_FILE_ROLE_LABELS:
        return normalized
    return "other"


def three_d_role_label(role: str | None) -> str:
    return THREE_D_FILE_ROLE_LABELS.get(normalize_three_d_role(role), THREE_D_FILE_ROLE_LABELS["other"])


def infer_three_d_role_from_filename(filename: str | None) -> str:
    name = (filename or "").lower()
    extension = name.rsplit(".", 1)[-1] if "." in name else ""
    if extension in {"glb", "gltf", "obj", "fbx", "stl", "usdz"}:
        return "model"
    if extension in {"ply", "las", "laz", "xyz", "pts"}:
        return "point_cloud"
    if extension in {"jpg", "jpeg", "png", "tif", "tiff", "bmp"}:
        return "oblique_photo"
    if extension in {"zip"}:
        return "support"
    return "other"


def _safe_filename(filename: str, *, fallback_prefix: str) -> str:
    clean_name = Path(filename).name or fallback_prefix
    if clean_name == ".":
        clean_name = fallback_prefix
    return clean_name


async def save_three_d_uploads(
    resource_dir: Path,
    uploads_by_role: Mapping[str, Sequence[UploadFile]],
) -> list[dict[str, Any]]:
    saved_files: list[dict[str, Any]] = []
    files_dir = resource_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    for role in THREE_D_FILE_ROLE_ORDER:
        uploads = list(uploads_by_role.get(role, ()))
        if not uploads:
            continue

        role_dir = files_dir / role
        role_dir.mkdir(parents=True, exist_ok=True)
        for index, upload in enumerate(uploads):
            original_filename = _safe_filename(upload.filename or f"{role}-{index}", fallback_prefix=f"{role}-{index}")
            stored_filename = original_filename
            stored_path = role_dir / stored_filename
            suffix = 1
            while stored_path.exists():
                stem = Path(original_filename).stem
                suffix_name = Path(original_filename).suffix
                stored_filename = f"{stem}-{suffix}{suffix_name}"
                stored_path = role_dir / stored_filename
                suffix += 1

            with stored_path.open("wb") as buffer:
                while chunk := await upload.read(64 * 1024):
                    buffer.write(chunk)

            saved_files.append(
                {
                    "role": role,
                    "role_label": three_d_role_label(role),
                    "filename": original_filename,
                    "actual_filename": stored_filename,
                    "file_path": str(stored_path),
                    "file_size": stored_path.stat().st_size,
                    "mime_type": upload.content_type,
                    "sort_order": len(saved_files),
                    "is_primary": False,
                }
            )

    return saved_files


def pick_primary_three_d_file(saved_files: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    if not saved_files:
        return None
    for preferred_role in ("model", "point_cloud", "oblique_photo", "texture", "support", "other"):
        for file_record in saved_files:
            if normalize_three_d_role(str(file_record.get("role"))) == preferred_role:
                return dict(file_record)
    return dict(saved_files[0])


def summarize_three_d_files(saved_files: Sequence[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    counts: dict[str, dict[str, Any]] = {}
    for file_record in saved_files:
        role = normalize_three_d_role(str(file_record.get("role")))
        summary = counts.setdefault(
            role,
            {
                "role": role,
                "role_label": three_d_role_label(role),
                "file_count": 0,
                "total_file_size": 0,
            },
        )
        summary["file_count"] += 1
        summary["total_file_size"] += int(file_record.get("file_size") or 0)

    group_summaries = list(counts.values())
    group_summaries.sort(key=lambda item: THREE_D_FILE_ROLE_ORDER.index(item["role"]) if item["role"] in THREE_D_FILE_ROLE_ORDER else len(THREE_D_FILE_ROLE_ORDER))
    if not group_summaries:
        return [], "暂无文件"
    parts = [f'{item["role_label"]} {item["file_count"]} 个' for item in group_summaries]
    return group_summaries, "、".join(parts)


def build_three_d_package_manifest(
    resource_dir: Path,
    *,
    asset: Any,
    metadata_layers: Mapping[str, Any],
    file_records: Sequence[Mapping[str, Any]],
) -> Path:
    manifest_path = resource_dir / "manifest.json"
    payload = {
        "resource_id": getattr(asset, "id", None),
        "title": metadata_layers.get("core", {}).get("title"),
        "resource_type": metadata_layers.get("core", {}).get("resource_type"),
        "profile_key": metadata_layers.get("core", {}).get("profile_key"),
        "profile_label": metadata_layers.get("core", {}).get("profile_label"),
        "file_count": len(file_records),
        "files": [
            {
                "role": file_record.get("role"),
                "role_label": file_record.get("role_label"),
                "filename": file_record.get("filename"),
                "actual_filename": file_record.get("actual_filename"),
                "file_path": file_record.get("file_path"),
                "file_size": file_record.get("file_size"),
                "mime_type": file_record.get("mime_type"),
                "is_primary": file_record.get("is_primary", False),
            }
            for file_record in file_records
        ],
        "metadata_layers": metadata_layers,
    }
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def build_three_d_download_zip(resource_dir: Path, zip_name: str, file_records: Sequence[Mapping[str, Any]]) -> Path:
    zip_path = resource_dir / zip_name
    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_record in file_records:
            file_path = Path(str(file_record.get("file_path") or ""))
            if not file_path.exists():
                continue
            archive.write(file_path, arcname=f"{file_record.get('role')}/{file_record.get('actual_filename')}")
    return zip_path


def remove_resource_tree(resource_dir: Path) -> None:
    if resource_dir.exists():
        shutil.rmtree(resource_dir, ignore_errors=True)
