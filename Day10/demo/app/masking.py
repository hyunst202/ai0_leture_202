import re
import sqlite3
import unicodedata

from flask import Blueprint, g, jsonify

from .auth import admin_required
from .db import get_db
from .validation import ApiError, checked_at, payload, source_url, text

bp = Blueprint("masking", __name__, url_prefix="/api/admin/masking-rules")
ASCII_LOWER = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")


def mask(value):
    if "masker" not in g:
        rows = get_db().execute("SELECT keyword,replacement FROM masking_rules ORDER BY length(keyword) DESC,id").fetchall()
        if not rows:
            g.masker = (None, {})
        else:
            expression = re.compile("|".join(re.escape(row["keyword"]) for row in rows), re.IGNORECASE | re.ASCII)
            g.masker = (expression, {row["keyword"].translate(ASCII_LOWER): row["replacement"] for row in rows})
    expression, replacements = g.masker
    if expression is None:
        return value
    value = unicodedata.normalize("NFC", value)
    return expression.sub(lambda match: replacements[match[0].translate(ASCII_LOWER)], value)


def rule_values(data):
    return (
        text(data.get("keyword"), "키워드", 100, trim=True),
        text(data.get("replacement", "***"), "치환 문자열", 100),
        source_url(data.get("source_url")),
        checked_at(data.get("source_checked_at")),
    )


@bp.get("")
@admin_required
def list_rules():
    rows = get_db().execute("SELECT * FROM masking_rules ORDER BY id DESC").fetchall()
    return jsonify(items=[dict(row) for row in rows])


@bp.post("")
@admin_required
def add_rule():
    data = payload(("keyword",), ("replacement", "source_url", "source_checked_at"))
    keyword, replacement, url, stamp = rule_values(data)
    db = get_db()
    try:
        with db:
            result = db.execute(
                "INSERT INTO masking_rules(keyword,replacement,source_url,source_checked_at,created_by) VALUES (?,?,?,?,?)",
                (keyword, replacement, url, stamp, g.user["id"]),
            )
    except sqlite3.IntegrityError:
        raise ApiError("이미 등록된 키워드입니다.", 409) from None
    return jsonify(id=result.lastrowid), 201


@bp.delete("/<int:rule_id>")
@admin_required
def delete_rule(rule_id):
    db = get_db()
    with db:
        result = db.execute("DELETE FROM masking_rules WHERE id=?", (rule_id,))
        if not result.rowcount:
            raise ApiError("규칙을 찾을 수 없습니다.", 404)
    return "", 204

