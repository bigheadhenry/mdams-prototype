from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

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
from .routers.platform import router as platform_router
from .routers.three_d import router as three_d_router
from .services.auth import seed_auth_data


def _ensure_asset_scope_columns() -> None:
    if engine.dialect.name != "sqlite":
        return

    inspector = inspect(engine)
    existing_columns = {column["name"] for column in inspector.get_columns("assets")}
    statements: list[str] = []
    if "visibility_scope" not in existing_columns:
        statements.append("ALTER TABLE assets ADD COLUMN visibility_scope VARCHAR DEFAULT 'open'")
    if "collection_object_id" not in existing_columns:
        statements.append("ALTER TABLE assets ADD COLUMN collection_object_id INTEGER")

    if not statements:
        return

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

# Initialize DB tables
Base.metadata.create_all(bind=engine)
_ensure_asset_scope_columns()
with SessionLocal() as session:
    seed_auth_data(session)

app = FastAPI(title="MEAM Prototype API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
app.include_router(three_d_router)
app.include_router(platform_router)
