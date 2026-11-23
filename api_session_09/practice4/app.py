"""App demo Practice 4: một URL POST /orders, gateway chọn v1 hoặc v2."""
import logging

from flask import Flask, jsonify, request

from gateway import CONFIG, config_snapshot, dispatch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
log = logging.getLogger("admin")

app = Flask(__name__)
app.json.ensure_ascii = False


@app.post("/orders")
def create_order():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify(error="body phải là JSON object, "
                             "nhớ gửi header Content-Type: application/json"), 400

    account_id = body.get("account_id")
    if not isinstance(account_id, str) or not account_id.strip():
        return jsonify(error="account_id (string) là bắt buộc"), 400

    amount = body.get("amount", 0)
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        return jsonify(error="amount phải là số"), 400

    which, reason, result = dispatch(body)

    resp = jsonify(result)
    # v1 (legacy) trả 200, v2 trả 201 Created — cũng là một thay đổi hành vi
    resp.status_code = 201 if which == "v2" else 200
    resp.headers["X-Order-Handler"] = which
    resp.headers["X-Route-Reason"] = reason
    return resp


# ---- "Dashboard" tối giản để đổi rollout khi đang chạy (CHỈ dùng cho demo) ----

@app.get("/admin/rollout")
def get_rollout():
    return jsonify(config_snapshot())


@app.post("/admin/rollout")
def set_rollout():
    if "percent" in request.args:
        try:
            pct = int(request.args["percent"])
        except ValueError:
            return jsonify(error="percent phải là số nguyên"), 400
        if not 0 <= pct <= 100:
            return jsonify(error="percent phải trong khoảng 0..100"), 400
        CONFIG["v2_percent"] = pct

    if "enabled" in request.args:
        raw = request.args["enabled"].lower()
        if raw not in {"true", "false"}:
            return jsonify(error="enabled phải là true hoặc false"), 400
        CONFIG["enabled"] = raw == "true"

    log.warning("rollout changed: %s", config_snapshot())
    return jsonify(config_snapshot())


if __name__ == "__main__":
    print(f"Rollout ban đầu: {config_snapshot()}")
    app.run(debug=True, port=5000)