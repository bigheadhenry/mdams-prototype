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
from .services.auth import seed_auth_data
from .services.three_d_demo_assets import seed_demo_three_d_assets
from .services.video_seed import seed_demo_video_asset


def _ensure_sqlite_schema_compatibility() -> None:
    if engine.dialect.name not in {"sqlite", "postgresql"}:
        return

    inspector = inspect(engine)
    existing_columns = {column["name"] for column in inspector.get_columns("assets")}
    statements: list[str] = []
    if "visibility_scope" not in existing_columns:
        statements.append("ALTER TABLE assets ADD COLUMN visibility_scope VARCHAR DEFAULT 'open'")
    if "collection_object_id" not in existing_columns:
        statements.append("ALTER TABLE assets ADD COLUMN collection_object_id INTEGER")
    if "image_record_id" not in existing_columns:
        statements.append("ALTER TABLE assets ADD COLUMN image_record_id INTEGER")

    if "image_records" in inspector.get_table_names():
        image_record_columns = {column["name"] for column in inspector.get_columns("image_records")}
        if "sheet_id" not in image_record_columns:
            statements.append("ALTER TABLE image_records ADD COLUMN sheet_id INTEGER")
        if "line_no" not in image_record_columns:
            statements.append("ALTER TABLE image_records ADD COLUMN line_no INTEGER")

    if "application_items" in inspector.get_table_names():
        application_item_columns = {column["name"] for column in inspector.get_columns("application_items")}
        application_item_column_specs = {
            "source_system": "VARCHAR",
            "source_id": "VARCHAR",
            "resource_type": "VARCHAR",
            "resource_title": "VARCHAR",
            "manifest_url": "VARCHAR",
            "source_label": "VARCHAR",
            "object_number": "VARCHAR",
        }
        for column_name, column_type in application_item_column_specs.items():
            if column_name not in application_item_columns:
                statements.append(f"ALTER TABLE application_items ADD COLUMN {column_name} {column_type}")
        if engine.dialect.name == "postgresql":
            asset_id_column = next(
                (column for column in inspector.get_columns("application_items") if column["name"] == "asset_id"),
                None,
            )
            if asset_id_column and not asset_id_column.get("nullable", True):
                statements.append("ALTER TABLE application_items ALTER COLUMN asset_id DROP NOT NULL")

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_assets_image_record_id "
                "ON assets(image_record_id) WHERE image_record_id IS NOT NULL"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_image_records_sheet_id "
                "ON image_records(sheet_id)"
            )
        )

# Initialize DB tables
Base.metadata.create_all(bind=engine)
_ensure_sqlite_schema_compatibility()
with SessionLocal() as session:
    seed_auth_data(session)
    seed_demo_three_d_assets(session)
    seed_demo_video_asset(session)

app = FastAPI(title="MEAM Prototype API")

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
app.include_router(platform_router)
