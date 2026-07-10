from pathlib import Path

from sqlalchemy.engine import make_url

import conftest as test_config


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_compose_requires_auth_password_and_keeps_built_frontend_assets():
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "AUTH_DEFAULT_PASSWORD=${AUTH_DEFAULT_PASSWORD:?" in compose
    assert "./frontend/dist:/usr/share/nginx/html" not in compose
    assert "http://localhost:8000/health" in compose
    assert "CANTALOUPE_INTERNAL_URL=http://cantaloupe:8182/iiif/2" in env_example


def test_application_has_no_known_default_admin_password():
    config_source = (REPO_ROOT / "backend/app/config.py").read_text(encoding="utf-8")

    assert 'AUTH_DEFAULT_PASSWORD = os.getenv("AUTH_DEFAULT_PASSWORD", "")' in config_source
    assert "mdams123" not in config_source


def test_container_database_alias_is_preserved(monkeypatch):
    monkeypatch.setenv(
        "TEST_DATABASE_URL",
        "postgresql://meam:test-password@db:5432/meam_db",
    )
    monkeypatch.delenv("PYTEST_DATABASE_URL", raising=False)
    monkeypatch.setattr(test_config, "_detect_reachable_database_url", lambda url: url)

    resolved = make_url(test_config._resolve_test_database_url())

    assert resolved.host == "db"
    assert resolved.database == "meam_db_test"


def test_missing_database_requires_explicit_skip_opt_in():
    conftest_source = (REPO_ROOT / "backend/tests/conftest.py").read_text(encoding="utf-8")

    assert '--allow-missing-services' in conftest_source
    assert "pytest.fail" in conftest_source


def test_alembic_urls_escape_configparser_percent_interpolation():
    env_source = (REPO_ROOT / "backend/alembic/env.py").read_text(encoding="utf-8")
    conftest_source = (REPO_ROOT / "backend/tests/conftest.py").read_text(encoding="utf-8")

    expected = 'replace("%", "%%")'
    assert expected in env_source
    assert expected in conftest_source


def test_deploy_health_check_uses_container_health_state():
    deploy_source = (REPO_ROOT / "deploy.sh").read_text(encoding="utf-8")

    assert "docker inspect --format" in deploy_source
    assert ".State.Health.Status" in deploy_source
    assert "awk '{print $2}'" not in deploy_source
