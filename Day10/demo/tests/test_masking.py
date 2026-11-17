from app import create_app
from conftest import send


def test_rule_changes_apply_to_existing_content_and_preserve_raw(app, writer, admin):
    post_id = send(writer, "/api/posts", data={"title": "TOKEN 글", "body": "TOKEN_LONG token .+"}).json["id"]
    assert send(writer, f"/api/posts/{post_id}/comments", data={"body": "Token"}).status_code == 201
    rules = []
    for keyword, replacement in [("TOKEN", "***"), ("TOKEN_LONG", "[긴표현]"), (".+", "정규식아님")]:
        added = send(admin, "/api/admin/masking-rules", data={"keyword": keyword, "replacement": replacement})
        assert added.status_code == 201
        rules.append(added.json["id"])
    assert writer.get("/api/posts").json["items"][0]["title"] == "*** 글"
    assert writer.get(f"/api/posts/{post_id}").json["item"]["body"] == "[긴표현] *** 정규식아님"
    assert writer.get(f"/api/posts/{post_id}/comments").json["items"][0]["body"] == "***"
    assert writer.get(f"/api/posts/{post_id}/edit").json["item"]["body"] == "TOKEN_LONG token .+"
    for rule_id in rules:
        assert send(admin, f"/api/admin/masking-rules/{rule_id}", "DELETE").status_code == 204
    assert writer.get(f"/api/posts/{post_id}").json["item"]["body"] == "TOKEN_LONG token .+"
    restarted = create_app(dict(app.config))
    assert restarted.test_client().get(f"/api/posts/{post_id}").json["item"]["title"] == "TOKEN 글"


def test_rules_are_admin_only(app, writer, admin):
    guest = app.test_client()
    assert guest.get("/api/admin/masking-rules").status_code == 401
    assert writer.get("/api/admin/masking-rules").status_code == 403
    assert send(writer, "/api/admin/masking-rules", data={"keyword": "x"}).status_code == 403
    assert send(writer, "/api/admin/masking-rules/1", "DELETE").status_code == 403
    assert send(admin, "/api/admin/masking-rules/999", "DELETE").status_code == 404


def test_rule_validation_and_literal_replacement(admin):
    assert send(admin, "/api/admin/masking-rules", data={"keyword": "   "}).status_code == 400
    assert send(admin, "/api/admin/masking-rules", data={"keyword": "x" * 101}).status_code == 400
    assert send(admin, "/api/admin/masking-rules", data={"keyword": "Meta"}).status_code == 201
    assert send(admin, "/api/admin/masking-rules", data={"keyword": " meta "}).status_code == 409
    for url in ("javascript:alert(1)", "https://[", "https://name:password@example.test"):
        assert send(admin, "/api/admin/masking-rules", data={"keyword": "url", "source_url": url}).status_code == 400
    assert send(admin, "/api/admin/masking-rules", data={"keyword": "date", "source_checked_at": "bad"}).status_code == 400


def test_replacement_not_reprocessed_and_unicode_case_is_not_collapsed(admin):
    for keyword, replacement in [("TOKEN", "NEXT"), ("NEXT", "DONE"), ("Σ", "UPPER"), ("σ", "lower")]:
        assert send(admin, "/api/admin/masking-rules", data={"keyword": keyword, "replacement": replacement}).status_code == 201
    post_id = send(admin, "/api/posts", data={"title": "TOKEN", "body": "Σ σ"}).json["id"]
    item = admin.get(f"/api/posts/{post_id}").json["item"]
    assert item["title"] == "NEXT" and item["body"] == "UPPER lower"

