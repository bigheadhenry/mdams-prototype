from pathlib import Path

import pytest

from app import config as app_config
from app.services import face_recognition_client
from app.services.local_face_recognition import LocalFaceRecognitionError


def _make_sample_file(tmp_path: Path) -> str:
    sample = tmp_path / "sample.jpg"
    sample.write_bytes(b"routing-tests-only")
    return str(sample)


def test_local_provider_dispatches_to_local_runtime(tmp_path, monkeypatch):
    sample_path = _make_sample_file(tmp_path)
    monkeypatch.setattr(app_config, "FACE_RECOGNITION_ENABLED", True)
    monkeypatch.setattr(app_config, "FACE_RECOGNITION_PROVIDER", "local")

    expected = {"status": "success", "count": 1, "results": [{"recognized": True}]}
    monkeypatch.setattr(
        face_recognition_client,
        "recognize_image_file_locally",
        lambda file_path, threshold=None, request_id=None: expected,
    )

    payload = face_recognition_client.recognize_image_file(
        sample_path,
        threshold=0.7,
        request_id="req-local",
    )

    assert payload == expected


def test_auto_provider_falls_back_to_remote_when_local_fails(tmp_path, monkeypatch):
    sample_path = _make_sample_file(tmp_path)
    monkeypatch.setattr(app_config, "FACE_RECOGNITION_ENABLED", True)
    monkeypatch.setattr(app_config, "FACE_RECOGNITION_PROVIDER", "auto")
    monkeypatch.setattr(app_config, "FACE_RECOGNITION_BASE_URL", "http://face-service")

    monkeypatch.setattr(
        face_recognition_client,
        "recognize_image_file_locally",
        lambda file_path, threshold=None, request_id=None: (_ for _ in ()).throw(
            LocalFaceRecognitionError("local bundle missing")
        ),
    )

    expected = {"status": "success", "count": 2, "results": [{"recognized": False}, {"recognized": True}]}
    monkeypatch.setattr(
        face_recognition_client,
        "_recognize_image_file_remote",
        lambda file_path, threshold=None, request_id=None: expected,
    )

    payload = face_recognition_client.recognize_image_file(
        sample_path,
        threshold=0.55,
        request_id="req-auto",
    )

    assert payload == expected


def test_local_provider_surfaces_local_runtime_errors(tmp_path, monkeypatch):
    sample_path = _make_sample_file(tmp_path)
    monkeypatch.setattr(app_config, "FACE_RECOGNITION_ENABLED", True)
    monkeypatch.setattr(app_config, "FACE_RECOGNITION_PROVIDER", "local")

    monkeypatch.setattr(
        face_recognition_client,
        "recognize_image_file_locally",
        lambda file_path, threshold=None, request_id=None: (_ for _ in ()).throw(
            LocalFaceRecognitionError("models not found")
        ),
    )

    with pytest.raises(face_recognition_client.FaceRecognitionClientError) as exc_info:
        face_recognition_client.recognize_image_file(sample_path)

    assert "models not found" in str(exc_info.value)
