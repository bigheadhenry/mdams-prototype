import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db

router = APIRouter(tags=["health"])


def build_health_payload(db: Session) -> dict:
    checks = {
        "database": {"status": "unknown"},
        "upload_dir": {
            "status": "healthy" if os.path.isdir(config.UPLOAD_DIR) else "unhealthy",
            "path": os.path.abspath(config.UPLOAD_DIR),
        },
    }

    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = "unhealthy"
        checks["database"]["error"] = str(exc)

    checks["database"]["status"] = db_status

    overall_status = "healthy" if all(item["status"] == "healthy" for item in checks.values()) else "degraded"
    http_status = 200 if overall_status == "healthy" else 503

    return {
        "status": overall_status,
        "service": "meam-prototype-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "http_status": http_status,
    }


def _health_response(db: Session):
    payload = build_health_payload(db)
    http_status = payload.pop("http_status")
    if http_status != 200:
        raise HTTPException(status_code=http_status, detail=payload)
    return payload


@router.get("/health")
def healthcheck(db: Session = Depends(get_db)):
    return _health_response(db)


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    return _health_response(db)
