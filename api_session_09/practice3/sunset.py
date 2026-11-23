"""
Practice 3 / 5 — Sunset middleware: decorator @deprecate_at

Trước ngày sunset : response bình thường + Sunset, Deprecation, Link header.
Từ ngày sunset    : 410 Gone, chỉ dẫn sang endpoint thay thế.
Mỗi lần gọi       : ghi log WARNING để đo còn ai đang dùng endpoint cũ.
"""
import logging
from datetime import datetime, timezone
from email.utils import format_datetime
from functools import wraps

from flask import jsonify, make_response, request

log = logging.getLogger("sunset")


def _now():
    """Thời gian hiện tại (UTC). Tách riêng để test có thể giả lập thời gian."""
    return datetime.now(timezone.utc)


def http_date(dt):
    """datetime -> HTTP-date, vd: 'Thu, 31 Dec 2026 23:59:59 GMT'."""
    return format_datetime(dt.astimezone(timezone.utc), usegmt=True)


def deprecate_at(sunset_date, replacement=None, deprecated_since=None):
    """
    sunset_date      : datetime CÓ timezone — thời điểm endpoint ngừng hoạt động.
    replacement      : URL thay thế, được phép chứa tham số route, vd "/api/v2/users/{uid}".
    deprecated_since : (tuỳ chọn) ngày bắt đầu deprecate. Nếu có, header Deprecation
                       dùng định dạng RFC 9745 "@<unix-timestamp>", nếu không dùng "true".
    """
    if sunset_date.tzinfo is None:
        raise ValueError("sunset_date phải có timezone, vd tzinfo=timezone.utc")

    sunset_str = http_date(sunset_date)
    deprecation_value = (
        f"@{int(deprecated_since.timestamp())}" if deprecated_since else "true"
    )

    def wrap(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            successor = replacement.format(**kwargs) if replacement else None

            if _now() >= sunset_date:
                # Sau sunset: KHÔNG gọi handler cũ nữa
                log.warning("gone_call path=%s client=%s",
                            request.path, request.remote_addr)
                r = jsonify(error="gone", sunset=sunset_str, use_instead=successor)
                r.status_code = 410
            else:
                # Trước sunset: chạy handler như bình thường, chỉ gắn thêm header
                log.warning("deprecated_call path=%s client=%s sunset=%s",
                            request.path, request.remote_addr, sunset_str)
                # make_response xử lý được dict, (dict, status) hoặc Response
                r = make_response(fn(*args, **kwargs))

            r.headers["Sunset"] = sunset_str
            r.headers["Deprecation"] = deprecation_value
            if successor:
                r.headers["Link"] = f'<{successor}>; rel="successor-version"'
            return r
        return inner
    return wrap