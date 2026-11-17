import sqlite3
from pathlib import Path

from flask import current_app, g

from .validation import ApiError


def get_db():
    if "db" not in g:
        path = Path(current_app.config["DATABASE_PATH"])
        if not path.is_file():
            raise ApiError("데이터베이스가 준비되지 않았습니다. 관리자가 init-db를 실행해야 합니다.", 503)
        connection = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        if connection.execute("PRAGMA user_version").fetchone()[0] != 2:
            connection.close()
            raise ApiError("데이터베이스 버전이 다릅니다. 백업 후 마이그레이션이 필요합니다.", 503)
        g.db = connection
    return g.db


def close_db(error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()

