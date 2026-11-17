import math
import re

from flask import Blueprint, g, jsonify, request

from .auth import login_required
from .db import get_db
from .masking import mask
from .validation import ApiError, payload, text

bp = Blueprint("board", __name__, url_prefix="/api/posts")
POST_SELECT = "SELECT p.*,u.nickname AS author FROM posts p JOIN users u ON u.id=p.author_id"


def get_post(post_id):
    row = get_db().execute(POST_SELECT + " WHERE p.id=?", (post_id,)).fetchone()
    if row is None:
        raise ApiError("게시글을 찾을 수 없습니다.", 404)
    return row


def require_owner(row):
    if row["author_id"] != g.user["id"]:
        raise ApiError("본인의 글만 수정하거나 삭제할 수 있습니다.", 403)


def serialize_post(row, *, detail=False):
    item = {key: row[key] for key in ("id", "author_id", "author", "created_at", "updated_at")}
    item["title"] = mask(row["title"])
    item["author"] = mask(row["author"])
    item["can_edit"] = g.user is not None and g.user["id"] == row["author_id"]
    if detail:
        item["body"] = mask(row["body"])
    return item


@bp.get("")
def list_posts():
    value = request.args.get("page", "1")
    if not re.fullmatch(r"[0-9]{1,9}", value) or int(value) < 1:
        raise ApiError("페이지는 1 이상의 정수여야 합니다.")
    db = get_db()
    total = db.execute("SELECT count(*) FROM posts").fetchone()[0]
    pages = max(1, math.ceil(total / 10))
    page = min(int(value), pages)
    rows = db.execute(POST_SELECT + " ORDER BY p.created_at DESC,p.id DESC LIMIT 10 OFFSET ?",
                      ((page - 1) * 10,)).fetchall()
    return jsonify(items=[serialize_post(row) for row in rows], total=total,
                   page=page, page_size=10, total_pages=pages)


@bp.post("")
@login_required
def create_post():
    data = payload(("title", "body"))
    title = text(data["title"], "제목", 200, trim=True)
    body = text(data["body"], "본문", 10000)
    db = get_db()
    with db:
        result = db.execute("INSERT INTO posts(author_id,title,body) VALUES (?,?,?)", (g.user["id"], title, body))
    return jsonify(id=result.lastrowid), 201


@bp.get("/<int:post_id>")
def detail(post_id):
    return jsonify(item=serialize_post(get_post(post_id), detail=True))


@bp.get("/<int:post_id>/edit")
@login_required
def edit(post_id):
    row = get_post(post_id)
    require_owner(row)
    return jsonify(item={key: row[key] for key in ("id", "title", "body")})


@bp.patch("/<int:post_id>")
@login_required
def update_post(post_id):
    data = payload(("title", "body"))
    title = text(data["title"], "제목", 200, trim=True)
    body = text(data["body"], "본문", 10000)
    db = get_db()
    with db:
        result = db.execute("UPDATE posts SET title=?,body=?,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=? AND author_id=?",
                            (title, body, post_id, g.user["id"]))
        if not result.rowcount:
            require_owner(get_post(post_id))
    return jsonify(message="수정했습니다.")


@bp.delete("/<int:post_id>")
@login_required
def delete_post(post_id):
    db = get_db()
    with db:
        result = db.execute("DELETE FROM posts WHERE id=? AND author_id=?", (post_id, g.user["id"]))
        if not result.rowcount:
            require_owner(get_post(post_id))
    return "", 204


@bp.get("/<int:post_id>/comments")
def list_comments(post_id):
    get_post(post_id)
    rows = get_db().execute(
        "SELECT c.id,c.body,c.created_at,c.author_id,u.nickname AS author FROM comments c JOIN users u ON u.id=c.author_id WHERE c.post_id=? ORDER BY c.created_at,c.id",
        (post_id,),
    ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["body"] = mask(item["body"])
        item["author"] = mask(item["author"])
        items.append(item)
    return jsonify(items=items)


@bp.post("/<int:post_id>/comments")
@login_required
def create_comment(post_id):
    data = payload(("body",))
    body = text(data["body"], "댓글", 1000)
    db = get_db()
    with db:
        get_post(post_id)
        result = db.execute("INSERT INTO comments(post_id,author_id,body) VALUES (?,?,?)", (post_id, g.user["id"], body))
    return jsonify(id=result.lastrowid), 201

