from __future__ import annotations

import py_compile
import subprocess
from pathlib import Path

from app.permissions import ROLE_PERMISSIONS
from app.routers import video as video_router
from app.services.auth import DEFAULT_USERS


REPO_ROOT = Path(__file__).resolve().parents[2]
REPLACEMENT_CHARACTER = "\ufffd"


def _route_permissions(router, path: str, method: str) -> set[str]:
    permissions: set[str] = set()
    for route in router.routes:
        if getattr(route, "path", None) != path or method.upper() not in getattr(route, "methods", set()):
            continue
        for dependency in route.dependant.dependencies:
            closure = getattr(dependency.call, "__closure__", None) or []
            for cell in closure:
                value = cell.cell_contents
                if isinstance(value, str):
                    permissions.add(value)
        return permissions
    raise AssertionError(f"Route not found: {method} {path}")


def _permissions_for_roles(roles: list[str]) -> set[str]:
    permissions: set[str] = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return permissions


def test_video_routes_and_default_roles_are_aligned():
    assert "video.view" in _route_permissions(video_router.router, "/video/resources", "GET")
    assert "video.view" in _route_permissions(video_router.router, "/video/resources/{asset_id}", "GET")
    assert "video.view" in _route_permissions(video_router.router, "/video/resources/{asset_id}/stream", "GET")
    assert "video.delete" in _route_permissions(video_router.router, "/video/resources/{asset_id}", "DELETE")

    users_by_name = {str(user["username"]): user for user in DEFAULT_USERS}
    expected_viewers = {
        "image_editor",
        "image_ingest",
        "image_review",
        "image_manager",
        "three_d_operator",
        "application_review",
        "collection_owner",
        "resource_user",
        "system_admin",
    }
    actual_viewers = {
        username
        for username, user in users_by_name.items()
        if "video.view" in _permissions_for_roles(list(user.get("roles", [])))
    }
    assert actual_viewers == expected_viewers

    actual_deleters = {
        username
        for username, user in users_by_name.items()
        if "video.delete" in _permissions_for_roles(list(user.get("roles", [])))
    }
    assert actual_deleters == {"image_manager", "system_admin"}


def test_redis_password_contract_is_consistent_across_compose_and_env_example():
    compose = (REPO_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    env_example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    assert "REDIS_PASSWORD=change_me_redis_password" in env_example
    assert "REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0" in env_example
    assert "redis-server --requirepass ${REDIS_PASSWORD}" in compose
    assert '"127.0.0.1:${REDIS_PORT}:6379"' in compose
    assert '"redis-cli", "-a", "${REDIS_PASSWORD}", "ping"' in compose


def test_merge_sensitive_python_files_are_valid_utf8_and_compile():
    for relative_path in [
        "backend/app/main.py",
        "backend/app/platform/image_source.py",
        "backend/app/permissions.py",
        "backend/app/routers/video.py",
        "backend/app/routers/ingest.py",
    ]:
        path = REPO_ROOT / relative_path
        path.read_text(encoding="utf-8")
        py_compile.compile(str(path), doraise=True)


def test_tracked_text_files_do_not_contain_replacement_characters():
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    text_suffixes = {".cfg", ".css", ".env", ".html", ".ini", ".js", ".json", ".md", ".py", ".sh", ".ts", ".tsx", ".txt", ".yml", ".yaml"}
    text_names = {".env.example", "Dockerfile"}
    offenders: list[str] = []

    for name in result.stdout.splitlines():
        path = REPO_ROOT / name
        if not path.is_file():
            continue
        if path.suffix not in text_suffixes and path.name not in text_names:
            continue
        try:
            contents = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            offenders.append(f"{name}: not valid UTF-8")
            continue
        if REPLACEMENT_CHARACTER in contents:
            offenders.append(f"{name}: contains U+FFFD replacement character")

    assert offenders == []
