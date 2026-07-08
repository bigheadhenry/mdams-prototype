import os
import socket
import struct
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

DEFAULT_POSTGRES_DATABASE_URL = "postgresql://meam:***@localhost:5432/meam_db"


def _render_url(url) -> str:
    return url.render_as_string(hide_password=False)


def _can_connect(url: str) -> bool:
    """Probe whether a PostgreSQL URL is reachable (network + credentials OK)."""
    engine = None
    try:
        engine = create_engine(url, connect_args={"connect_timeout": 2})
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
    finally:
        if engine is not None:
            engine.dispose()


def _default_gateway_ips() -> list[str]:
    """Return likely docker bridge gateway IPs from /proc/net/route plus common defaults."""
    gateways: list[str] = []
    try:
        with open("/proc/net/route") as f:
            for line in f:
                parts = line.split()
                if len(parts) < 4:
                    continue
                if parts[0] == "Iface":
                    continue
                try:
                    flags = int(parts[3], 16)
                except ValueError:
                    continue
                if flags & 0x0003 == 0x0003:  # RTF_UP | RTF_GATEWAY
                    gateway_hex = parts[2]
                    gateway = socket.inet_ntoa(struct.pack("<L", int(gateway_hex, 16)))
                    if gateway not in gateways:
                        gateways.append(gateway)
    except Exception:
        pass
    for fallback in ("172.17.0.1", "172.20.0.1", "172.18.0.1", "172.19.0.1"):
        if fallback not in gateways:
            gateways.append(fallback)
    return gateways


def _docker_postgres_host(port: int = 5432) -> str | None:
    """Ask Docker for the published host:port of a container named meam-db."""
    try:
        output = subprocess.check_output(
            ["docker", "port", "meam-db", str(port)],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
        # docker port returns something like "0.0.0.0:5432/tcp" or "127.0.0.1:5432/tcp"
        for line in output.splitlines():
            host_port = line.split("/")[0]
            if ":" in host_port:
                host, prt = host_port.rsplit(":", 1)
                if host in ("0.0.0.0", "::"):
                    host = "127.0.0.1"
                return f"{host}:{prt}"
    except Exception:
        pass
    return None


def _detect_reachable_database_url(database_url: str) -> str:
    """Rewrite localhost/db aliases to an actually reachable docker bridge host when needed."""
    parsed = make_url(database_url)
    if not parsed.drivername.startswith("postgresql"):
        return database_url

    original = _render_url(parsed)
    if _can_connect(original):
        return original

    candidates = [original]

    # Docker-published port (works when docker CLI is available)
    docker_host_port = _docker_postgres_host(parsed.port or 5432)
    if docker_host_port:
        candidates.append(_render_url(parsed.set(host=docker_host_port.rsplit(":", 1)[0], port=int(docker_host_port.rsplit(":", 1)[1]))))

    # Common docker bridge gateways
    for gateway in _default_gateway_ips():
        candidates.append(_render_url(parsed.set(host=gateway)))

    for candidate in candidates:
        if _can_connect(candidate):
            return candidate

    # If nothing is reachable, return the original and let the caller raise a clear error.
    return original


def _resolve_test_database_url() -> str:
    explicit_url = os.getenv("TEST_DATABASE_URL") or os.getenv("PYTEST_DATABASE_URL")
    base_url = explicit_url or os.getenv("DATABASE_URL", DEFAULT_POSTGRES_DATABASE_URL)

    # Make sure we are pointing at a real, reachable PostgreSQL host.
    base_url = _detect_reachable_database_url(base_url)

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


def _run_alembic_migrations(database_url: str) -> None:
    """Apply all Alembic migrations to the test database."""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_cfg, "head")


def _truncate_all_tables(connection) -> None:
    """Reset data between tests without dropping the Alembic-managed schema."""
    table_names = [t.name for t in Base.metadata.sorted_tables]
    if not table_names:
        return
    # CASCADE handles foreign keys; RESTART IDENTITY resets sequences.
    connection.execute(text(f"TRUNCATE {', '.join(table_names)} RESTART IDENTITY CASCADE"))


TEST_DATABASE_URL = _resolve_test_database_url()
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("MDAMS_DEMO_MODE", "1")

from app import config as app_config  # noqa: E402
from app.database import Base  # noqa: E402
import app.models  # noqa: E402, F401 — populate Base.metadata

# Enable legacy header auth for tests so existing tests using
# get_current_user(x_mdams_user=...) continue to work.
app_config.LEGACY_HEADER_AUTH_ENABLED = True


@pytest.fixture()
def test_upload_dir(tmp_path, monkeypatch):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    monkeypatch.setattr(app_config, "UPLOAD_DIR", str(upload_dir))
    return upload_dir


@pytest.fixture(scope="session")
def db_engine():
    engine = None
    try:
        _ensure_postgres_database_exists(TEST_DATABASE_URL)
        engine = create_engine(TEST_DATABASE_URL)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        if engine is not None:
            engine.dispose()
        pytest.skip(f"PostgreSQL test database unavailable: {exc}")

    # Bring the test DB schema up to date via real migrations instead of
    # Base.metadata.create_all, so tests exercise the same schema path as prod.
    try:
        _run_alembic_migrations(TEST_DATABASE_URL)
    except Exception as exc:
        if engine is not None:
            engine.dispose()
        pytest.skip(f"Alembic migration failed for test database: {exc}")

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    # Give each test a clean data slate while keeping the migrated schema.
    with db_engine.begin() as connection:
        _truncate_all_tables(connection)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
