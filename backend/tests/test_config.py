import os

from app import config


def test_load_dotenv_prefers_nearest_parent(tmp_path, monkeypatch):
    repo_root = tmp_path / "repo"
    backend_dir = repo_root / "backend"
    app_dir = backend_dir / "app"
    app_dir.mkdir(parents=True)
    (repo_root / ".git").mkdir()

    (repo_root / ".env").write_text(
        "DOTENV_TEST_VALUE=root\nDOTENV_ROOT_ONLY=root\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        "DOTENV_TEST_VALUE=outer\nDOTENV_OUTER_ONLY=outer\n",
        encoding="utf-8",
    )
    (backend_dir / ".env").write_text(
        "DOTENV_TEST_VALUE=backend\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("DOTENV_LOADED", raising=False)
    monkeypatch.delenv("DOTENV_TEST_VALUE", raising=False)
    monkeypatch.delenv("DOTENV_ROOT_ONLY", raising=False)

    config._load_dotenv(app_dir / "config.py")

    assert os.environ["DOTENV_TEST_VALUE"] == "backend"
    assert os.environ.get("DOTENV_ROOT_ONLY") is None
    assert os.environ.get("DOTENV_OUTER_ONLY") is None
    assert os.environ["DOTENV_LOADED"] == "1"
