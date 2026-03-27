import os
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException


os.environ.setdefault("DATABASE_URL", "sqlite:///./test_health.db")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app import main  # noqa: E402
from app import config as app_config  # noqa: E402


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

    payload = main.build_health_payload(HealthyDB())

    assert payload["status"] == "healthy"
    assert payload["checks"]["database"]["status"] == "healthy"
    assert payload["checks"]["upload_dir"]["status"] == "healthy"
    assert payload["http_status"] == 200


def test_healthcheck_raises_503_when_database_fails():
    with pytest.raises(HTTPException) as exc_info:
        main.healthcheck(db=BrokenDB())

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["status"] == "degraded"
    assert exc_info.value.detail["checks"]["database"]["status"] == "unhealthy"


def test_readiness_raises_503_when_upload_dir_is_missing(monkeypatch):
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(Path.cwd() / "missing-upload-dir"))

    with pytest.raises(HTTPException) as exc_info:
        main.readiness(db=HealthyDB())

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail["checks"]["upload_dir"]["status"] == "unhealthy"
