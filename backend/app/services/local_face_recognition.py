from __future__ import annotations

import json
import os
import pickle
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .. import config


class LocalFaceRecognitionError(RuntimeError):
    pass


def _path_mtime(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _normalize_vector(value: Any):
    try:
        import numpy as np
    except ImportError as exc:
        raise LocalFaceRecognitionError(
            "numpy is required for local face recognition. Install backend/requirements.txt first."
        ) from exc

    vector = np.asarray(value, dtype=np.float32)
    if vector.ndim != 1:
        vector = vector.reshape(-1)
    return vector / (np.linalg.norm(vector) + 1e-10)


def _confidence_from_score(score: float) -> float:
    return float(max(0.0, min(1.0, (score - 0.2) / 0.6)))


def _as_bbox(value: Any) -> list[int]:
    if value is None:
        return []
    if hasattr(value, "astype"):
        value = value.astype(int).tolist()
    elif isinstance(value, tuple):
        value = list(value)
    if not isinstance(value, list):
        return []
    bbox: list[int] = []
    for item in value[:4]:
        try:
            bbox.append(int(item))
        except (TypeError, ValueError):
            bbox.append(0)
    return bbox


def _as_landmarks(value: Any) -> list[list[float]]:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        value = value.tolist()
    if not isinstance(value, list):
        return []
    landmarks: list[list[float]] = []
    for pair in value:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        try:
            landmarks.append([float(pair[0]), float(pair[1])])
        except (TypeError, ValueError):
            continue
    return landmarks


def _ensure_local_models(model_root: Path, model_name: str) -> None:
    model_dir = model_root / "models" / model_name
    required_files = {
        "det_10g.onnx",
        "w600k_r50.onnx",
        "1k3d68.onnx",
        "2d106det.onnx",
        "genderage.onnx",
    }

    if not model_dir.exists():
        raise LocalFaceRecognitionError(
            f"Local face model directory not found: {model_dir}. "
            "Put the InsightFace bundle under runtime/face_recognition/models/<model_name>/."
        )

    existing = {path.name for path in model_dir.glob("*.onnx")}
    missing = sorted(required_files - existing)
    if missing:
        raise LocalFaceRecognitionError(
            f"Local face model files are missing in {model_dir}: {', '.join(missing)}"
        )


class _InsightFaceRuntime:
    def __init__(self, *, model_root: str, model_name: str, strict_local_models: bool):
        try:
            import cv2
            import numpy as np
            import onnxruntime
            from insightface.app import FaceAnalysis
        except ImportError as exc:
            raise LocalFaceRecognitionError(
                "Local face recognition dependencies are missing. "
                "Install insightface, onnxruntime, numpy, and opencv-python-headless."
            ) from exc

        self._cv2 = cv2
        self._np = np
        self._model_root = Path(model_root).expanduser().resolve()
        self._model_name = model_name

        if strict_local_models:
            _ensure_local_models(self._model_root, self._model_name)

        available_providers = onnxruntime.get_available_providers()
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        self._app = FaceAnalysis(name=self._model_name, root=str(self._model_root), providers=providers)

        ctx_id = 0 if "CUDAExecutionProvider" in available_providers else -1
        self._app.prepare(ctx_id=ctx_id, det_size=(640, 640))

    def analyze(self, image_path: str) -> list[Any]:
        img = self._cv2.imread(image_path)
        if img is None:
            try:
                img_array = self._np.fromfile(image_path, dtype=self._np.uint8)
                img = self._cv2.imdecode(img_array, self._cv2.IMREAD_COLOR)
            except Exception:
                img = None

        if img is None:
            raise LocalFaceRecognitionError(f"Could not load image for local face recognition: {image_path}")

        try:
            return list(self._app.get(img))
        except Exception as exc:
            raise LocalFaceRecognitionError(f"InsightFace inference failed: {exc}") from exc


@dataclass(frozen=True)
class _FaceIndexSnapshot:
    index_dir: Path
    meta_mtime: float | None
    embeddings_mtime: float | None
    clusters: dict[str, dict[str, Any]]
    centers: dict[str, Any]

    def format_person_info(self, cluster_id: str | None) -> dict[str, Any] | None:
        if not cluster_id:
            return None
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return None

        representative = cluster.get("representative_face")
        return {
            "id": cluster_id,
            "name": cluster.get("name"),
            "face_count": int(cluster.get("count") or 0),
            "representative_face_url": f"/faces/{representative}.jpg" if representative else None,
        }


_RUNTIME_LOCK = threading.Lock()
_RUNTIME_CACHE: tuple[tuple[str, str, bool], _InsightFaceRuntime] | None = None

_INDEX_LOCK = threading.Lock()
_INDEX_CACHE: _FaceIndexSnapshot | None = None


def _runtime_key() -> tuple[str, str, bool]:
    return (
        str(config.FACE_RECOGNITION_MODEL_ROOT),
        str(config.FACE_RECOGNITION_MODEL_NAME),
        bool(config.FACE_RECOGNITION_STRICT_LOCAL_MODELS),
    )


def _get_runtime() -> _InsightFaceRuntime:
    global _RUNTIME_CACHE

    key = _runtime_key()
    with _RUNTIME_LOCK:
        if _RUNTIME_CACHE is not None and _RUNTIME_CACHE[0] == key:
            return _RUNTIME_CACHE[1]

        runtime = _InsightFaceRuntime(
            model_root=key[0],
            model_name=key[1],
            strict_local_models=key[2],
        )
        _RUNTIME_CACHE = (key, runtime)
        return runtime


def _build_index_snapshot(index_dir: Path) -> _FaceIndexSnapshot:
    meta_path = index_dir / "meta.json"
    embeddings_path = index_dir / "embeddings.pkl"

    if meta_path.exists():
        try:
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LocalFaceRecognitionError(f"Failed to load face index metadata from {meta_path}: {exc}") from exc
    else:
        metadata = {"clusters": {}, "faces": {}}

    if embeddings_path.exists():
        try:
            with embeddings_path.open("rb") as file_obj:
                embeddings = pickle.load(file_obj)
        except Exception as exc:
            raise LocalFaceRecognitionError(f"Failed to load face embeddings from {embeddings_path}: {exc}") from exc
    else:
        embeddings = {}

    raw_clusters = metadata.get("clusters")
    clusters = raw_clusters if isinstance(raw_clusters, dict) else {}
    centers: dict[str, Any] = {}

    for cluster_id, cluster in clusters.items():
        if not isinstance(cluster, dict):
            continue
        face_ids = cluster.get("face_ids")
        if not isinstance(face_ids, list):
            continue
        vectors = [_normalize_vector(embeddings[face_id]) for face_id in face_ids if face_id in embeddings]
        if not vectors:
            continue

        try:
            import numpy as np
        except ImportError as exc:
            raise LocalFaceRecognitionError(
                "numpy is required for local face recognition. Install backend/requirements.txt first."
            ) from exc

        mean_vector = np.mean(vectors, axis=0)
        centers[str(cluster_id)] = _normalize_vector(mean_vector)

    return _FaceIndexSnapshot(
        index_dir=index_dir,
        meta_mtime=_path_mtime(meta_path),
        embeddings_mtime=_path_mtime(embeddings_path),
        clusters={str(key): value for key, value in clusters.items() if isinstance(value, dict)},
        centers=centers,
    )


def _get_face_index(index_dir: str) -> _FaceIndexSnapshot:
    global _INDEX_CACHE

    resolved_index_dir = Path(index_dir).expanduser().resolve()
    meta_path = resolved_index_dir / "meta.json"
    embeddings_path = resolved_index_dir / "embeddings.pkl"
    current_meta_mtime = _path_mtime(meta_path)
    current_embeddings_mtime = _path_mtime(embeddings_path)

    with _INDEX_LOCK:
        if (
            _INDEX_CACHE is not None
            and _INDEX_CACHE.index_dir == resolved_index_dir
            and _INDEX_CACHE.meta_mtime == current_meta_mtime
            and _INDEX_CACHE.embeddings_mtime == current_embeddings_mtime
        ):
            return _INDEX_CACHE

        snapshot = _build_index_snapshot(resolved_index_dir)
        _INDEX_CACHE = snapshot
        return snapshot


def recognize_image_file_locally(
    file_path: str,
    *,
    threshold: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    if not file_path or not os.path.exists(file_path):
        raise LocalFaceRecognitionError(f"Recognition source file does not exist: {file_path}")

    try:
        import numpy as np
    except ImportError as exc:
        raise LocalFaceRecognitionError(
            "numpy is required for local face recognition. Install backend/requirements.txt first."
        ) from exc

    runtime = _get_runtime()
    face_index = _get_face_index(config.FACE_RECOGNITION_INDEX_DIR)
    faces = runtime.analyze(file_path)
    effective_threshold = float(
        threshold if threshold is not None else config.FACE_RECOGNITION_THRESHOLD
    )

    results: list[dict[str, Any]] = []
    for index, face in enumerate(faces):
        embedding = getattr(face, "normed_embedding", None)
        if embedding is None:
            embedding = getattr(face, "embedding", None)

        if embedding is None:
            feature = np.zeros((512,), dtype=np.float32)
        else:
            feature = _normalize_vector(embedding)

        best_score = -1.0
        best_cluster_id: str | None = None
        for cluster_id, center in face_index.centers.items():
            score = float(np.dot(feature, center))
            if score > best_score:
                best_score = score
                best_cluster_id = cluster_id

        recognized = bool(best_cluster_id) and best_score >= effective_threshold
        person_info = face_index.format_person_info(best_cluster_id) if recognized else None
        results.append(
            {
                "face_index": index,
                "bbox": _as_bbox(getattr(face, "bbox", None)),
                "landmarks": _as_landmarks(getattr(face, "kps", None)),
                "recognized": recognized,
                "person_info": person_info,
                "score": float(best_score),
                "confidence": _confidence_from_score(best_score),
            }
        )

    return {
        "status": "success",
        "mode": "local_runtime",
        "filename": os.path.basename(file_path),
        "request_id": request_id,
        "count": len(results),
        "results": results,
    }
