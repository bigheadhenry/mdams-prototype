from pathlib import Path

import pytest
from fastapi import HTTPException

from app import config as app_config  # noqa: E402
from app.routers import health as health_router


pytestmark = [pytest.mark.smoke, pytest.mark.integration]


class HealthyDB:
    def execute(self, _statement):
        return None


class BrokenDB:
    def execute(self, _statement):
        raise RuntimeError("database unavailable")


def test_health_payload_reports_healthy_state(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(upload_dir))

    payload = health_router.build_health_payload(HealthyDB())

    assert payload["status"] == "healthy"
    assert payload["checks"]["database"]["status"] == "healthy"
    assert payload["checks"]["upload_dir"]["status"] == "healthy"
    assert payload["http_status"] == 200


def test_healthcheck_raises_503_when_database_fails():
    with pytest.raises(HTTPException) as exc_info:
        health_router.healthcheck(db=BrokenDB())

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["status"] == "degraded"
    assert exc_info.value.detail["checks"]["database"]["status"] == "unhealthy"


def test_readiness_raises_503_when_upload_dir_is_missing(monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(Path.cwd() / "missing-upload-dir"))

    with pytest.raises(HTTPException) as exc_info:
        health_router.readiness(db=HealthyDB())

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["checks"]["upload_dir"]["status"] == "unhealthy"
