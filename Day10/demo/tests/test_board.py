import sqlite3

import pytest

from conftest import login, send, signup


def create(writer, title="첫 기록", body="첫 줄\n둘째 줄"):
    result = send(writer, "/api/posts", data={"title": title, "body": body})
    assert result.status_code == 201
    return result.json["id"]


@pytest.mark.parametrize("count,expected", [(0, [0]), (1, [1]), (10, [10]), (11, [10, 1]), (21, [10, 10, 1])])
def test_pagination_and_stable_order(app, writer, count, expected):
    user_id = writer.get("/api/auth/me").json["user"]["id"]
    with sqlite3.connect(app.config["DATABASE_PATH"]) as db:
        db.executemany("INSERT INTO posts(author_id,title,body,created_at) VALUES (?,?,?,'2026-10-28T00:00:00.000Z')",
                       [(user_id, f"글 {index}", "본문") for index in range(count)])
    ids = []
    for page, length in enumerate(expected, 1):
        result = writer.get(f"/api/posts?page={page}").json
        assert len(result["items"]) == length
        assert result["total"] == count and result["page_size"] == 10
        ids.extend(item["id"] for item in result["items"])
    assert ids == sorted(ids, reverse=True)
    assert writer.get("/api/posts?page=9999").json["page"] == len(expected)


@pytest.mark.parametrize("page", ["0", "-1", "x", "1.5", "9999999999999999"])
def test_invalid_page(client, page):
    assert client.get(f"/api/posts?page={page}").status_code == 400


def test_owner_edit_delete_and_comment_cascade(app, writer):
    post_id = create(writer)
    other = app.test_client()
    assert signup(other, "other@example.test", "다른 회원").status_code == 201
    assert login(other, "other@example.test").status_code == 200
    assert send(other, f"/api/posts/{post_id}/comments", data={"body": "댓글"}).status_code == 201
    assert other.get(f"/api/posts/{post_id}/edit").status_code == 403
    assert send(other, f"/api/posts/{post_id}", "PATCH", {"title": "침범", "body": "본문"}).status_code == 403
    assert send(other, f"/api/posts/{post_id}", "DELETE").status_code == 403
    assert send(writer, f"/api/posts/{post_id}", "PATCH", {"title": "수정", "body": "수정\n내용"}).status_code == 200
    assert writer.get(f"/api/posts/{post_id}/edit").json["item"]["body"] == "수정\n내용"
    assert send(writer, f"/api/posts/{post_id}", "DELETE").status_code == 204
    assert writer.get(f"/api/posts/{post_id}").status_code == 404
    with sqlite3.connect(app.config["DATABASE_PATH"]) as db:
        assert db.execute("SELECT count(*) FROM comments").fetchone()[0] == 0


@pytest.mark.parametrize("title,body", [(" ", "본문"), ("제목", "\n\t\u3000"), ("x" * 201, "B"), ("T", "x" * 10001)])
def test_empty_or_long_post_rejected(writer, title, body):
    assert send(writer, "/api/posts", data={"title": title, "body": body}).status_code == 400


def test_unicode_html_and_linebreaks_are_data(writer):
    raw = "<script>alert('x')</script>\n😀 한글"
    post_id = create(writer, "😀" * 200, raw)
    detail = writer.get(f"/api/posts/{post_id}")
    assert detail.content_type.startswith("application/json")
    assert detail.json["item"]["body"] == raw
    assert len(detail.json["item"]["title"]) == 200
    assert "body" not in writer.get("/api/posts").json["items"][0]


def test_comments_are_scoped_and_require_login(app, writer):
    one, two = create(writer), create(writer)
    guest = app.test_client()
    assert send(guest, f"/api/posts/{one}/comments", data={"body": "C"}).status_code == 401
    assert send(writer, f"/api/posts/{one}/comments", data={"body": "\t\n"}).status_code == 400
    assert send(writer, f"/api/posts/{one}/comments", data={"body": "x" * 1001}).status_code == 400
    assert send(writer, f"/api/posts/{one}/comments", data={"body": "첫 댓글"}).status_code == 201
    assert len(guest.get(f"/api/posts/{one}/comments").json["items"]) == 1
    assert guest.get(f"/api/posts/{two}/comments").json["items"] == []
    assert guest.get("/api/posts/999/comments").status_code == 404


def test_author_id_injection_rejected(writer):
    assert send(writer, "/api/posts", data={"title": "T", "body": "B", "author_id": 999}).status_code == 400


def test_last_page_deletion_clamps_to_previous_page(writer):
    for _ in range(11):
        create(writer)
    last = writer.get("/api/posts?page=2").json["items"][0]["id"]
    assert send(writer, f"/api/posts/{last}", "DELETE").status_code == 204
    result = writer.get("/api/posts?page=2").json
    assert result["page"] == 1 and len(result["items"]) == 10


def test_missing_resource_statuses(writer):
    assert writer.get("/api/posts/999").status_code == 404
    assert send(writer, "/api/posts/999", "PATCH", {"title": "T", "body": "B"}).status_code == 404
    assert send(writer, "/api/posts/999", "DELETE").status_code == 404

