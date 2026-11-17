import sqlite3
from datetime import timedelta

import pytest
from werkzeug.security import check_password_hash

from app import create_app
from conftest import login, send, signup


def test_signup_normalizes_email_and_stores_only_hash(app, client):
    result = signup(client, "  Writer@Example.Test  ")
    assert result.status_code == 201
    assert result.json["user"]["role"] == "USER"
    assert "password" not in result.get_data(as_text=True)
    with sqlite3.connect(app.config["DATABASE_PATH"]) as db:
        address, digest = db.execute("SELECT email,password_hash FROM users").fetchone()
    assert address == "writer@example.test"
    assert digest != "TestPassword123!" and check_password_hash(digest, "TestPassword123!")
    assert signup(client, "WRITER@example.test").status_code == 409


@pytest.mark.parametrize("field,value", [
    ("email", "bad"), ("email", "a@b..test"), ("email", "a..b@example.test"),
    ("nickname", "\u3000\n\t"), ("nickname", "가" * 31),
    ("password", "short"), ("password", "x" * 129), ("password", " " * 8),
])
def test_signup_validation(client, field, value):
    data = {"email": "person@example.test", "nickname": "작성자", "password": "TestPassword123!"}
    data[field] = value
    assert send(client, "/api/auth/signup", data=data).status_code == 400


def test_role_injection_and_non_json_rejected(client):
    data = {"email": "person@example.test", "nickname": "작성자", "password": "TestPassword123!", "role": "ADMIN"}
    assert send(client, "/api/auth/signup", data=data).status_code == 400
    assert send(client, "/api/auth/signup").status_code == 400


def test_individual_passwords_and_failure_message(client):
    assert signup(client).status_code == 201
    assert signup(client, "second@example.test", password="DifferentPassword123!").status_code == 201
    wrong = login(client, password="WrongPassword123!")
    missing = login(client, "unknown@example.test")
    assert wrong.status_code == missing.status_code == 401
    assert wrong.json == missing.json
    assert login(client, "second@example.test").status_code == 401
    assert login(client, "second@example.test", "DifferentPassword123!").status_code == 200


def test_session_survives_app_recreation_but_logout_revokes_old_cookie(app, writer):
    cookie = writer.get_cookie("session").value
    restarted = create_app(dict(app.config))
    browser = restarted.test_client()
    browser.set_cookie("session", cookie)
    assert browser.get("/api/auth/me").json["user"]["email"] == "writer@example.test"
    assert send(writer, "/api/auth/logout").status_code == 200
    attacker = restarted.test_client()
    attacker.set_cookie("session", cookie)
    assert attacker.get("/api/auth/me").json["user"] is None
    assert send(attacker, "/api/posts", data={"title": "T", "body": "B"}).status_code == 401


def test_new_login_revokes_previous_login(app, writer):
    second = app.test_client()
    assert login(second).status_code == 200
    assert writer.get("/api/auth/me").json["user"] is None
    assert second.get("/api/auth/me").json["user"] is not None


def test_tampered_and_expired_cookie_rejected(app, writer, monkeypatch):
    cookie = writer.get_cookie("session").value
    browser = app.test_client()
    browser.set_cookie("session", cookie + "tampered")
    assert browser.get("/api/auth/me").json["user"] is None
    import itsdangerous.timed
    clock = itsdangerous.timed.time.time
    monkeypatch.setattr(itsdangerous.timed.time, "time", lambda: clock() + 9 * 3600)
    assert writer.get("/api/auth/me").json["user"] is None


def test_password_recovery_is_only_mock(writer, app):
    before = writer.get_cookie("session").value
    result = send(writer, "/api/auth/forgot-password", data={"email": "writer@example.test"})
    assert result.status_code == 200 and result.json["mock"] is True
    assert "실제 이메일은 발송되지" in result.json["message"]
    assert login(writer).status_code == 200
    assert before


@pytest.mark.parametrize("path,method,data", [
    ("/api/auth/signup", "POST", {}), ("/api/auth/login", "POST", {}),
    ("/api/auth/logout", "POST", None), ("/api/posts", "POST", {}),
    ("/api/posts/1", "PATCH", {}), ("/api/posts/1", "DELETE", None),
    ("/api/posts/1/comments", "POST", {}), ("/api/admin/masking-rules", "POST", {}),
    ("/api/admin/masking-rules/1", "DELETE", None),
])
def test_csrf_missing_or_forged_is_rejected(client, path, method, data):
    assert client.open(path, method=method, json=data).status_code == 400
    assert client.open(path, method=method, json=data, headers={"X-CSRFToken": "forged"}).status_code == 400


def test_production_cookie_flags(app, client):
    assert signup(client).status_code == 201
    production = create_app({**dict(app.config), "APP_ENV": "production"})
    browser = production.test_client()
    csrf = browser.get("/api/auth/csrf", base_url="https://localhost").json["csrf_token"]
    result = browser.post("/api/auth/login", base_url="https://localhost", headers={"X-CSRFToken": csrf, "Referer": "https://localhost/"},
                          json={"email": "writer@example.test", "password": "TestPassword123!"})
    assert result.status_code == 200
    cookie = result.headers["Set-Cookie"]
    assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=Lax" in cookie
    assert production.config["DEBUG"] is False
    assert production.config["PERMANENT_SESSION_LIFETIME"] == timedelta(hours=8)

