import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

DEFAULT_POSTGRES_DATABASE_URL = "postgresql://meam:meam_secret@localhost:5432/meam_db"


def _render_url(url) -> str:
    return url.render_as_string(hide_password=False)


def _resolve_test_database_url() -> str:
    explicit_url = os.getenv("TEST_DATABASE_URL") or os.getenv("PYTEST_DATABASE_URL")
    if explicit_url:
        return explicit_url

    base_url = os.getenv("DATABASE_URL", DEFAULT_POSTGRES_DATABASE_URL)
    parsed = make_url(base_url)
    host = parsed.host or "localhost"
    if host in {"db", "postgres", "postgresql"}:
        parsed = parsed.set(host="localhost")

    database_name = parsed.database or "meam_db"
    if not database_name.endswith("_test"):
        database_name = f"{database_name}_test"

    return _render_url(parsed.set(database=database_name))


def _build_admin_database_url(database_url: str) -> str:
    parsed = make_url(database_url)
    return _render_url(parsed.set(database=os.getenv("TEST_DATABASE_ADMIN_DB", "postgres")))


def _ensure_postgres_database_exists(database_url: str) -> None:
    parsed = make_url(database_url)
    if not parsed.drivername.startswith("postgresql"):
        raise RuntimeError(
            f"Pytest database must be PostgreSQL, got: {parsed.drivername}. "
            "Set TEST_DATABASE_URL to a PostgreSQL test database."
        )

    database_name = parsed.database
    if not database_name:
        raise RuntimeError("Pytest database URL must include a database name.")

    admin_engine = create_engine(_build_admin_database_url(database_url), isolation_level="AUTOCOMMIT")
    quoted_database_name = database_name.replace('"', '""')
    try:
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": database_name},
            ).scalar()
            if not exists:
                connection.execute(text(f'CREATE DATABASE "{quoted_database_name}"'))
    finally:
        admin_engine.dispose()


TEST_DATABASE_URL = _resolve_test_database_url()
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app import config as app_config  # noqa: E402
from app.database import Base  # noqa: E402


@pytest.fixture()
def test_upload_dir(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(upload_dir))
    return upload_dir


@pytest.fixture(scope="session")
def db_engine():
    try:
        _ensure_postgres_database_exists(TEST_DATABASE_URL)
        engine = create_engine(TEST_DATABASE_URL)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL test database unavailable: {exc}")

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    Base.metadata.drop_all(bind=db_engine)
    Base.metadata.create_all(bind=db_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
