import hashlib
import importlib
import json
import sqlite3
from pathlib import Path

import pytest

from app import create_app
from app.config import ROOT
from conftest import send


def test_init_refuses_existing_db_and_import_is_explicit(app):
    path = Path(app.config["DATABASE_PATH"])
    before = hashlib.sha256(path.read_bytes()).digest()
    result = app.test_cli_runner().invoke(args=["init-db"])
    assert result.exit_code != 0
    assert hashlib.sha256(path.read_bytes()).digest() == before
    assert app.test_client().get("/api/posts").json["items"] == []


def test_rule_import_and_backup_are_safe(app, tmp_path):
    runner = app.test_cli_runner()
    result = runner.invoke(args=["import-rules", str(ROOT / "seed" / "masking-rules.json")])
    assert result.exit_code == 0 and "5개 추가" in result.output
    again = runner.invoke(args=["import-rules", str(ROOT / "seed" / "masking-rules.json")])
    assert again.exit_code == 0 and "0개 추가" in again.output
    target = tmp_path / "backup.sqlite3"
    assert runner.invoke(args=["backup-db", str(target)]).exit_code == 0
    with sqlite3.connect(target) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("SELECT count(*) FROM masking_rules").fetchone()[0] == 5
        assert db.execute("PRAGMA user_version").fetchone()[0] == 2
    assert runner.invoke(args=["backup-db", str(target)]).exit_code != 0
    assert runner.invoke(args=["backup-db", str(ROOT / "app" / "static" / "private.sqlite3")]).exit_code != 0


def test_import_validates_entire_file_before_changes(app, tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps([{"keyword": "GOOD"}, {"keyword": " "}]), encoding="utf-8")
    assert app.test_cli_runner().invoke(args=["import-rules", str(path)]).exit_code != 0
    with sqlite3.connect(app.config["DATABASE_PATH"]) as db:
        assert db.execute("SELECT count(*) FROM masking_rules").fetchone()[0] == 0


def test_admin_creation_does_not_publish_password_or_promote_existing_user(app, admin):
    result = app.test_cli_runner().invoke(args=["create-admin", "--email", "admin@example.test", "--nickname", "중복"],
                                         input="AnotherPassword123!\nAnotherPassword123!\n")
    assert result.exit_code != 0 and "AnotherPassword123!" not in result.output
    assert admin.get("/api/auth/me").json["user"]["role"] == "ADMIN"


def test_static_and_private_file_routing(client):
    assert client.get("/").status_code == 200
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
    for path in ("/.env", "/database-schema.sql", "/instance/note-demo.sqlite3", "/static/../.env", "/plan.md"):
        assert client.get(path).status_code == 404
    result = client.get("/")
    assert result.headers["X-Content-Type-Options"] == "nosniff"
    assert "script-src 'self'" in result.headers["Content-Security-Policy"]
    assert "innerHTML" not in (ROOT / "app" / "static" / "app.js").read_text(encoding="utf-8")


def test_wsgi_import_does_not_create_db_or_start_server(app, tmp_path, monkeypatch):
    target = tmp_path / "must-not-be-created.sqlite3"
    monkeypatch.setenv("SECRET_KEY", "wsgi-test-key-" * 5)
    monkeypatch.setenv("DATABASE_PATH", str(target))
    monkeypatch.setenv("APP_ENV", "production")
    import flask
    monkeypatch.setattr(flask.Flask, "run", lambda *args, **kwargs: pytest.fail("server started on import"))
    import wsgi
    module = importlib.reload(wsgi)
    assert not target.exists() and module.application.config["SESSION_COOKIE_SECURE"] is True
    assert module.application.test_client().get("/api/posts").status_code == 503
    assert not target.exists()


def test_configuration_rejects_missing_secret_and_relative_path(app):
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({**dict(app.config), "SECRET_KEY": None})
    with pytest.raises(RuntimeError, match="absolute"):
        create_app({**dict(app.config), "DATABASE_PATH": "relative.sqlite3"})
    with pytest.raises(RuntimeError, match="outside"):
        create_app({**dict(app.config), "DATABASE_PATH": str(ROOT / "app" / "static" / "bad.sqlite3")})


def test_schema_constraints_and_database_connections(app):
    from app.db import get_db
    with app.app_context():
        db = get_db()
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA journal_mode").fetchone()[0] != "wal"
        assert db.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO users(email,nickname,password_hash) VALUES ('x@example.test','X',NULL)")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO posts(author_id,title,body) VALUES (999,'T','B')")


def test_request_size_limit_and_no_store(client):
    result = send(client, "/api/auth/signup", data={"large": "x" * 70000})
    assert result.status_code == 413
    assert client.get("/api/auth/csrf").headers["Cache-Control"] == "no-store"


def test_source_archive_excludes_secrets_databases_and_runtimes(tmp_path):
    from scripts.package import package
    from zipfile import ZipFile
    target = package(tmp_path / "source.zip")
    with ZipFile(target) as archive:
        names = archive.namelist()
        assert "README.md" in names and "wsgi.py" in names and ".env.example" in names
        assert "app/static/index.html" in names and "database-schema.sql" in names
        assert ".env" not in names
        assert not any(name.startswith(("instance/", ".venv/", "private-backups/")) for name in names)
        assert not any(name.endswith((".sqlite3", ".db", ".pyc")) for name in names)

