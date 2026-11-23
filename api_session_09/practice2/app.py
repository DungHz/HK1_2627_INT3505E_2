"""
Practice 2 / 5 — Header versioning với decorator @api_version

Cùng URL GET /users/<id> phục vụ nhiều phiên bản.
Client chọn version qua header X-API-Version.
Server trả header X-API-Version-Served để debug.
"""
from functools import wraps

from flask import Flask, jsonify, request

LATEST = "2"                              # newest stable, dùng khi client không gửi header
SUPPORTED = {"1", "2", "2024-06-20"}      # các version server chấp nhận

USERS = {
    1: {"f": "Văn", "l": "Nguyễn", "e": "a@vnu.vn"},
    2: {"f": "Trang", "l": "Trần", "e": "b@vnu.vn"},
}

app = Flask(__name__)
app.json.ensure_ascii = False             # trả tiếng Việt có dấu thay vì \u00e3...


def api_version(supported=SUPPORTED, default=LATEST):
    """Decorator đọc X-API-Version và truyền version vào handler (tham số đầu tiên)."""
    def decorate(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # ① Thiếu header (hoặc header rỗng) -> dùng default
            v = (request.headers.get("X-API-Version") or default).strip()

            # ④ Version lạ -> 400, KHÔNG fallback
            if v not in supported:
                resp = jsonify(
                    error="unsupported version",
                    requested=v,
                    supported=sorted(supported),
                )
                resp.status_code = 400
                resp.headers["Vary"] = "X-API-Version"
                return resp

            # Handler có thể trả dict hoặc (dict, status)
            result = fn(v, *args, **kwargs)
            body, status = result if isinstance(result, tuple) else (result, 200)

            response = jsonify(body)
            response.status_code = status
            # ② Cho client / ops biết server thực sự phục vụ version nào
            response.headers["X-API-Version-Served"] = v
            # Báo cho cache/CDN: response khác nhau theo header này
            response.headers["Vary"] = "X-API-Version"
            return response
        return wrapper
    return decorate


@app.route("/users/<int:uid>")
@api_version()
def get_user(version, uid):
    u = USERS.get(uid)
    if not u:
        return {"error": "not found"}, 404

    # ③ Mỗi version một shape response
    if version == "1":
        return {"id": uid, "full_name": f"{u['f']} {u['l']}"}

    # "2" và "2024-06-20" dùng chung schema v2
    return {
        "id": uid,
        "first_name": u["f"],
        "last_name": u["l"],
        "email": u["e"],
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)