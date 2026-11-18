import logging
from datetime import datetime, timezone
from email.utils import format_datetime

from flask import Blueprint, current_app, jsonify, request

from . import users_data as db

bp = Blueprint("v1", __name__)
log = logging.getLogger("deprecation")

# Thông báo 18/11/2026 -> sunset 31/05/2027 (>= 180 ngày, tránh cuối quý)
DEFAULT_SUNSET = datetime(2027, 5, 31, 23, 59, 59, tzinfo=timezone.utc)
DEPRECATED_SINCE = datetime(2026, 11, 18, tzinfo=timezone.utc)
SUCCESSOR = "/api/v2/users"


def _sunset():
    return current_app.config.get("V1_SUNSET", DEFAULT_SUNSET)


@bp.before_request
def gone_after_sunset():
    if datetime.now(timezone.utc) >= _sunset():
        return jsonify(error="gone",
                       sunset=format_datetime(_sunset(), usegmt=True),
                       use_instead=SUCCESSOR), 410
    log.warning("deprecated_call %s %s", request.path, request.remote_addr)


@bp.after_request
def add_deprecation_headers(resp):
    resp.headers["Sunset"] = format_datetime(_sunset(), usegmt=True)        # RFC 8594
    resp.headers["Deprecation"] = f"@{int(DEPRECATED_SINCE.timestamp())}"  # RFC 9745
    resp.headers["Link"] = f'<{SUCCESSOR}>; rel="successor-version"'
    return resp


@bp.get("/users/<int:uid>")
def get_user(uid):
    u = db.get_user(uid)
    if not u:
        return jsonify(error="not_found"), 404
    return jsonify(id=uid,
                   full_name=f"{u['first_name']} {u['last_name']}",
                   email=u["email"])