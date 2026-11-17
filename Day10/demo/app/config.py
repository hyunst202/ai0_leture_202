import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def configuration(overrides=None):
    load_dotenv(ROOT / ".env", override=False)
    environment = os.environ.get("APP_ENV", "development")
    values = {
        "APP_ENV": environment,
        "SECRET_KEY": os.environ.get("SECRET_KEY"),
        "DATABASE_PATH": os.environ.get("DATABASE_PATH") or (
            str(ROOT / "instance" / "note-demo.sqlite3") if environment == "development" else None
        ),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "PERMANENT_SESSION_LIFETIME": timedelta(hours=8),
        "MAX_CONTENT_LENGTH": 64 * 1024,
        "DEBUG": False,
    }
    values.update(overrides or {})
    if values["APP_ENV"] not in {"development", "production", "testing"}:
        raise RuntimeError("APP_ENV must be development, production, or testing")
    secret = values["SECRET_KEY"]
    if not isinstance(secret, str) or len(secret) < 32:
        raise RuntimeError("SECRET_KEY must be at least 32 characters; run scripts/configure.py")
    database = values["DATABASE_PATH"]
    if not database or not Path(database).is_absolute():
        raise RuntimeError("DATABASE_PATH must be an absolute file path")
    resolved = Path(database).resolve()
    static = (ROOT / "app" / "static").resolve()
    if static == resolved or static in resolved.parents:
        raise RuntimeError("DATABASE_PATH must be outside the public static directory")
    values["DATABASE_PATH"] = str(resolved)
    values["SESSION_COOKIE_SECURE"] = values["APP_ENV"] == "production"
    return values

