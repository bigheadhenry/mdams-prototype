import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from . import config
from .database import Base, engine
from .database import SessionLocal
from .routers.auth import router as auth_router
from .routers.assets import router as assets_router
from .routers.applications import router as applications_router
from .routers.ai_mirador import router as ai_mirador_router
from .routers.downloads import router as downloads_router
from .routers.health import build_health_payload, healthcheck, readiness, router as health_router
from .routers.iiif import router as iiif_router
from .routers.ingest import router as ingest_router
from .routers.image_records import router as image_records_router
from .routers.platform import router as platform_router
from .routers.three_d import router as three_d_router
from .routers.video import router as video_router
from .routers.cart import router as cart_router
from .routers.subscriptions import router as subscriptions_router
from .services.auth import seed_auth_data
from .services.three_d_demo_assets import seed_demo_three_d_assets
from .services.video_seed import seed_demo_video_asset

logger = logging.getLogger(__name__)


def _migrate_if_new() -> None:
    """Apply Alembic migrations on first startup (empty DB).
    
    Keeps the legacy `_ensure_sqlite_schema_compatibility()` approach as a
    fallback for environments where Alembic is unavailable (e.g. test runners
    without the dev dependency installed).
    """
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if existing_tables:
        # Database already has tables — schema migration is Alembic's job now.
        # The old inline _ensure_sqlite_schema_compatibility() has been removed
        # in favor of proper Alembic migrations.
        return
    
    # New database: let Alembic create the full schema.
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config( str(Path(__file__).resolve().parent.parent / "alembic.ini") )
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migration applied (empty DB → head).")
    except Exception:
        # Fallback: create all tables directly (Alembic not installed / configured).
        logger.warning("Alembic unavailable — falling back to Base.metadata.create_all.")
        Base.metadata.create_all(bind=engine)


from pathlib import Path  # noqa: E402 — imported here for alembic config path resolution above

# Initialize DB tables
_migrate_if_new()

with SessionLocal() as session:
    seed_auth_data(session)
    seed_demo_three_d_assets(session)
    seed_demo_video_asset(session)

app = FastAPI(title="MDAMS Prototype API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(assets_router)
app.include_router(applications_router)
app.include_router(ai_mirador_router)
app.include_router(iiif_router)
app.include_router(downloads_router)
app.include_router(ingest_router)
app.include_router(image_records_router)
app.include_router(three_d_router)
app.include_router(video_router)
app.include_router(cart_router)
app.include_router(subscriptions_router)
app.include_router(platform_router)

# ── Search engine init ───────────────────────────────────────────
from .services.search_engine.engine import init_engine, seed_index_from_adapters
from .database import SessionLocal

@app.on_event("startup")
async def _init_search_engine():
    init_engine()
    try:
        with SessionLocal() as session:
            seed_index_from_adapters(session)
    except Exception:
        pass  # Non-blocking — search falls back to adapter filtering
