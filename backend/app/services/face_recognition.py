from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Mapping


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_name(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_bbox(value: object) -> list[int]:
    if not isinstance(value, (list, tuple)):
        return []
    bbox: list[int] = []
    for item in value[:4]:
        try:
            bbox.append(int(item))
        except (TypeError, ValueError):
            bbox.append(0)
    return bbox


def _normalize_float(value: object | None, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def build_face_recognition_pending_state(
    *,
    asset_id: int,
    threshold: float,
) -> dict[str, Any]:
    return {
        "status": "pending",
        "provider": "face_founding",
        "threshold": threshold,
        "asset_id": asset_id,
        "last_run_at": _iso_now(),
        "face_count": 0,
        "recognized_count": 0,
        "recognized_names": [],
        "faces": [],
    }


def build_face_recognition_failed_state(
    *,
    asset_id: int,
    threshold: float,
    error_message: str,
) -> dict[str, Any]:
    return {
        "status": "failed",
        "provider": "face_founding",
        "threshold": threshold,
        "asset_id": asset_id,
        "last_run_at": _iso_now(),
        "face_count": 0,
        "recognized_count": 0,
        "recognized_names": [],
        "faces": [],
        "error_message": error_message,
    }


def normalize_face_recognition_response(
    payload: Mapping[str, Any],
    *,
    asset_id: int,
    threshold: float,
    image_width: int | None = None,
    image_height: int | None = None,
) -> dict[str, Any]:
    raw_results = payload.get("results")
    results = raw_results if isinstance(raw_results, list) else []
    faces: list[dict[str, Any]] = []
    recognized_names: list[str] = []

    for index, item in enumerate(results):
        if not isinstance(item, Mapping):
            continue
        person_info = item.get("person_info")
        person_info_dict = person_info if isinstance(person_info, Mapping) else {}
        name = _clean_name(person_info_dict.get("name"))
        recognized = bool(item.get("recognized")) and bool(name)
        if recognized and name:
            recognized_names.append(name)

        faces.append(
            {
                "face_index": int(item.get("face_index", index) or index),
                "name": name,
                "recognized": recognized,
                "confidence": _normalize_float(item.get("confidence")),
                "score": _normalize_float(item.get("score"), default=-1.0),
                "bbox": _normalize_bbox(item.get("bbox")),
                "cluster_id": _clean_name(person_info_dict.get("id")),
            }
        )

    ordered_names = _unique_preserve_order(recognized_names)
    face_count = int(payload.get("count") or len(faces))
    normalized: dict[str, Any] = {
        "status": "success" if face_count > 0 else "no_face",
        "provider": "face_founding",
        "threshold": threshold,
        "asset_id": asset_id,
        "last_run_at": _iso_now(),
        "face_count": face_count,
        "recognized_count": len(ordered_names),
        "recognized_names": ordered_names,
        "faces": faces,
        "raw_response": deepcopy(dict(payload)),
    }
    if image_width and image_width > 0:
        normalized["image_width"] = int(image_width)
    if image_height and image_height > 0:
        normalized["image_height"] = int(image_height)
    return normalized
