import os
from pathlib import Path


def _load_dotenv(current_path: Path | None = None) -> None:
    """Best-effort load of a local .env file without external dependencies."""
    if os.getenv("DOTENV_LOADED") == "1":
        return

    resolved_path = (current_path or Path(__file__)).resolve()

    # Walk outward from the current file so the closest .env wins.
    for parent in resolved_path.parents:
        env_path = parent / ".env"
        if not env_path.exists():
            if (parent / ".git").exists() or ((parent / "backend").exists() and (parent / "frontend").exists()):
                break
            continue
        try:
            for raw_line in env_path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and os.environ.get(key) in (None, ""):
                    os.environ[key] = value
            os.environ["DOTENV_LOADED"] = "1"
            return
        except OSError:
            if (parent / ".git").exists() or ((parent / "backend").exists() and (parent / "frontend").exists()):
                break
            continue


_load_dotenv()

BACKEND_ROOT = Path(__file__).resolve().parents[1]
FACE_RUNTIME_ROOT = (BACKEND_ROOT / "runtime" / "face_recognition").resolve()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://meam:meam_secret@db:5432/meam_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
API_PUBLIC_URL = os.getenv("API_PUBLIC_URL", "http://localhost:3000/api")
CANTALOUPE_PUBLIC_URL = os.getenv("CANTALOUPE_PUBLIC_URL", "http://localhost:8182/iiif/2")
CANTALOUPE_INTERNAL_URL = os.getenv("CANTALOUPE_INTERNAL_URL") or CANTALOUPE_PUBLIC_URL

# Moonshot (Kimi) is OpenAI-compatible. Keep the OPENAI_* names for backwards
# compatibility, but default them to Moonshot when dedicated Moonshot values are
# not provided.
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY", "")
MOONSHOT_BASE_URL = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
MOONSHOT_MODEL = os.getenv("MOONSHOT_MODEL", "kimi-k2.5")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", MOONSHOT_API_KEY)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", MOONSHOT_BASE_URL)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", MOONSHOT_MODEL)
OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))

FACE_RECOGNITION_ENABLED = os.getenv("FACE_RECOGNITION_ENABLED", "0") == "1"
FACE_RECOGNITION_PROVIDER = os.getenv("FACE_RECOGNITION_PROVIDER", "local").strip().lower()
FACE_RECOGNITION_BASE_URL = os.getenv("FACE_RECOGNITION_BASE_URL", "http://host.docker.internal:8010")
FACE_RECOGNITION_TIMEOUT_SECONDS = float(os.getenv("FACE_RECOGNITION_TIMEOUT_SECONDS", "30"))
FACE_RECOGNITION_THRESHOLD = float(os.getenv("FACE_RECOGNITION_THRESHOLD", "0.5"))
FACE_RECOGNITION_MODEL_ROOT = os.getenv("FACE_RECOGNITION_MODEL_ROOT", str(FACE_RUNTIME_ROOT))
FACE_RECOGNITION_MODEL_NAME = os.getenv("FACE_RECOGNITION_MODEL_NAME", "buffalo_l")
FACE_RECOGNITION_INDEX_DIR = os.getenv(
    "FACE_RECOGNITION_INDEX_DIR",
    str((FACE_RUNTIME_ROOT / "index").resolve()),
)
FACE_RECOGNITION_STRICT_LOCAL_MODELS = os.getenv("FACE_RECOGNITION_STRICT_LOCAL_MODELS", "1") == "1"
