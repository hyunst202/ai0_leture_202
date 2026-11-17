import sqlite3
from functools import wraps

from flask import Blueprint, g, jsonify, session
from flask_wtf.csrf import generate_csrf
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_db
from .validation import ApiError, email, password, payload, text

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def public_user(user):
    return {key: user[key] for key in ("id", "email", "nickname", "role")} if user else None


def load_user():
    g.user = None
    user_id = session.get("user_id")
    if user_id is not None:
        user = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user is not None and session.get("auth_version") == user["auth_version"]:
            g.user = user
        else:
            session.clear()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            raise ApiError("로그인이 필요합니다.", 401)
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if g.user["role"] != "ADMIN":
            raise ApiError("관리자만 사용할 수 있습니다.", 403)
        return view(*args, **kwargs)
    return wrapped


@bp.get("/csrf")
def csrf_token():
    return jsonify(csrf_token=generate_csrf())


@bp.get("/me")
def me():
    return jsonify(user=public_user(g.user))


@bp.post("/signup")
def signup():
    data = payload(("email", "nickname", "password"))
    address = email(data["email"])
    nickname = text(data["nickname"], "닉네임", 30, trim=True)
    digest = generate_password_hash(password(data["password"]))
    db = get_db()
    try:
        with db:
            result = db.execute(
                "INSERT INTO users(email,nickname,password_hash,role) VALUES (?,?,?,'USER')",
                (address, nickname, digest),
            )
    except sqlite3.IntegrityError:
        raise ApiError("이미 가입된 이메일입니다.", 409) from None
    user = db.execute("SELECT * FROM users WHERE id=?", (result.lastrowid,)).fetchone()
    return jsonify(user=public_user(user)), 201


@bp.post("/login")
def login():
    data = payload(("email", "password"))
    address = email(data["email"])
    supplied = password(data["password"])
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email=?", (address,)).fetchone()
    if user is None or not check_password_hash(user["password_hash"], supplied):
        raise ApiError("이메일 또는 비밀번호가 올바르지 않습니다.", 401)
    with db:
        db.execute("UPDATE users SET auth_version=auth_version+1 WHERE id=?", (user["id"],))
        version = db.execute("SELECT auth_version FROM users WHERE id=?", (user["id"],)).fetchone()[0]
    session.clear()
    session.permanent = True
    session["user_id"] = user["id"]
    session["auth_version"] = version
    return jsonify(user=public_user(user))


@bp.post("/logout")
@login_required
def logout():
    db = get_db()
    with db:
        db.execute("UPDATE users SET auth_version=auth_version+1 WHERE id=? AND auth_version=?",
                   (g.user["id"], session["auth_version"]))
    session.clear()
    return jsonify(message="로그아웃했습니다.")


@bp.post("/forgot-password")
def forgot_password():
    data = payload(("email",))
    email(data["email"])
    return jsonify(mock=True, message="비밀번호 찾기는 데모 기능입니다. 실제 이메일은 발송되지 않으며 비밀번호도 변경되지 않습니다.")

