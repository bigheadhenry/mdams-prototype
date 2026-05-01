from __future__ import annotations

import os
from typing import Any

import httpx

from .. import config
from .local_face_recognition import LocalFaceRecognitionError, recognize_image_file_locally


class FaceRecognitionClientError(RuntimeError):
    pass


def _remote_candidate_urls(base_url: str) -> list[str]:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/recognize"):
        return [normalized]

    candidates = [
        f"{normalized}/recognize",
        f"{normalized}/api/recognize",
        f"{normalized}/external/recognize",
        f"{normalized}/api/external/recognize",
    ]

    unique_candidates: list[str] = []
    for candidate in candidates:
        if candidate not in unique_candidates:
            unique_candidates.append(candidate)
    return unique_candidates


def _recognize_image_file_remote(
    file_path: str,
    *,
    threshold: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    base_url = (config.FACE_RECOGNITION_BASE_URL or "").strip()
    if not base_url:
        raise FaceRecognitionClientError("FACE_RECOGNITION_BASE_URL is not configured for remote recognition")

    headers = {"X-Request-ID": request_id} if request_id else None
    params = {"threshold": threshold if threshold is not None else config.FACE_RECOGNITION_THRESHOLD}
    last_error: Exception | None = None

    with open(file_path, "rb") as file_stream:
        files = {
            "file": (
                os.path.basename(file_path),
                file_stream,
                "application/octet-stream",
            )
        }
        response = None
        for url in _remote_candidate_urls(base_url):
            try:
                file_stream.seek(0)
                response = httpx.post(
                    url,
                    params=params,
                    files=files,
                    headers=headers,
                    timeout=config.FACE_RECOGNITION_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                break
            except httpx.HTTPError as exc:
                last_error = exc
                response = None

        if response is None:
            raise FaceRecognitionClientError(f"Face recognition request failed: {last_error}") from last_error

    try:
        payload = response.json()
    except ValueError as exc:
        raise FaceRecognitionClientError("Face recognition service returned invalid JSON") from exc

    if not isinstance(payload, dict):
        raise FaceRecognitionClientError("Face recognition service returned an unexpected payload")

    if payload.get("status") not in {None, "success"}:
        raise FaceRecognitionClientError(str(payload.get("detail") or payload.get("message") or "Face recognition failed"))

    return payload


def recognize_image_file(
    file_path: str,
    *,
    threshold: float | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    if not config.FACE_RECOGNITION_ENABLED:
        raise FaceRecognitionClientError("Face recognition is disabled")

    if not file_path or not os.path.exists(file_path):
        raise FaceRecognitionClientError(f"Recognition source file does not exist: {file_path}")

    provider = (config.FACE_RECOGNITION_PROVIDER or "local").strip().lower()
    if provider not in {"local", "remote", "auto"}:
        provider = "local"

    errors: list[str] = []

    if provider in {"local", "auto"}:
        try:
            return recognize_image_file_locally(
                file_path,
                threshold=threshold,
                request_id=request_id,
            )
        except LocalFaceRecognitionError as exc:
            if provider == "local":
                raise FaceRecognitionClientError(f"Local face recognition failed: {exc}") from exc
            errors.append(f"local={exc}")

    if provider in {"remote", "auto"}:
        try:
            return _recognize_image_file_remote(
                file_path,
                threshold=threshold,
                request_id=request_id,
            )
        except FaceRecognitionClientError as exc:
            errors.append(f"remote={exc}")

    if errors:
        raise FaceRecognitionClientError(" ; ".join(errors))
    raise FaceRecognitionClientError("No face recognition provider is available")
