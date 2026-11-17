import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlsplit

from flask import request


class ApiError(Exception):
    def __init__(self, message, status=400):
        self.message = message
        self.status = status
        super().__init__(message)


def payload(required, optional=()):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("JSON 형식의 입력이 필요합니다.")
    if set(data) - set(required) - set(optional):
        raise ApiError("허용하지 않는 입력 항목이 있습니다.")
    if set(required) - set(data):
        raise ApiError("필수 입력 항목을 확인해주세요.")
    return data


def text(value, label, limit, *, trim=False):
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ApiError(f"{label}을(를) 입력해주세요.")
    if trim:
        value = unicodedata.normalize("NFC", value.strip())
    if len(value) > limit:
        raise ApiError(f"{label}은(는) {limit:,}자 이하로 입력해주세요.")
    return value


def email(value):
    value = text(value, "이메일", 254, trim=True).lower()
    parts = value.split("@")
    if len(parts) != 2:
        raise ApiError("이메일 형식을 확인해주세요.")
    local, domain = parts
    labels = domain.split(".")
    if (len(local) > 64 or not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+", local)
            or local.startswith(".") or local.endswith(".") or ".." in local
            or len(labels) < 2
            or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                   for label in labels)):
        raise ApiError("이메일 형식을 확인해주세요. 영문 이메일 주소를 사용해주세요.")
    return value


def password(value):
    if not isinstance(value, str) or not 8 <= len(value) <= 128 or not value.strip() or "\x00" in value:
        raise ApiError("비밀번호는 8~128자로 입력해주세요.")
    return value


def source_url(value):
    if value is None or value == "":
        return None
    if not isinstance(value, str) or len(value) > 2048 or any(c.isspace() for c in value):
        raise ApiError("출처 URL 형식을 확인해주세요.")
    try:
        parsed = urlsplit(value)
    except ValueError:
        raise ApiError("출처 URL 형식을 확인해주세요.") from None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ApiError("출처는 http 또는 https URL로 입력해주세요.")
    return value


def checked_at(value):
    if value is None or value == "":
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError
        return stamp.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    except (ValueError, TypeError, AttributeError):
        raise ApiError("자료 확인 시각은 시간대가 있는 ISO 8601 형식이어야 합니다.") from None

