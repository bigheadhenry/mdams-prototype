from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers.assets import router as assets_router
from .routers.applications import router as applications_router
from .routers.downloads import router as downloads_router
from .routers.health import build_health_payload, healthcheck, readiness, router as health_router
from .routers.iiif import router as iiif_router
from .routers.ingest import router as ingest_router
from .routers.platform import router as platform_router
from .routers.three_d import router as three_d_router

# Initialize DB tables
Base.metadata.create_all(bind=engine)

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
app.include_router(assets_router)
app.include_router(applications_router)
app.include_router(iiif_router)
app.include_router(downloads_router)
app.include_router(ingest_router)
app.include_router(three_d_router)
app.include_router(platform_router)
