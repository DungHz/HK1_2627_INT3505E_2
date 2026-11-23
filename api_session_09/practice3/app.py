"""App demo cho Practice 3: v1 bị deprecate, v2 là bản thay thế."""
import logging
import os
from datetime import datetime, timezone

from flask import Flask

from sunset import deprecate_at

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

USERS = {
    1: {"first_name": "Văn", "last_name": "Nguyễn", "email": "a@vnu.vn"},
    2: {"first_name": "Trang", "last_name": "Trần", "email": "b@vnu.vn"},
}


def _load_sunset():
    """Mặc định 31/12/2026. Có thể ghi đè bằng biến môi trường V1_SUNSET để demo 410."""
    raw = os.environ.get("V1_SUNSET")
    if not raw:
        return datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    dt = datetime.fromisoformat(raw)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


V1_SUNSET = _load_sunset()

app = Flask(__name__)
app.json.ensure_ascii = False


@app.route("/api/v1/users/<int:uid>")
@deprecate_at(V1_SUNSET, replacement="/api/v2/users/{uid}")
def get_v1(uid):
    u = USERS.get(uid)
    if not u:
        return {"error": "not found"}, 404
    return {"id": uid, "full_name": f"{u['first_name']} {u['last_name']}"}


@app.route("/api/v2/users/<int:uid>")
def get_v2(uid):
    u = USERS.get(uid)
    if not u:
        return {"error": "not found"}, 404
    return {"id": uid, **u}


if __name__ == "__main__":
    print(f"V1 sunset: {V1_SUNSET.isoformat()}")
    app.run(debug=True, port=5000)