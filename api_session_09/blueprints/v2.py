from flask import Blueprint, jsonify, request, url_for

from . import users_data as db

bp = Blueprint("v2", __name__)
REQUIRED = ("first_name", "last_name", "email")


def serialize(uid, u):
    return {"id": uid, "first_name": u["first_name"],
            "last_name": u["last_name"], "email": u["email"]}


@bp.get("/users/<int:uid>")
def get_user(uid):
    u = db.get_user(uid)
    if not u:
        return jsonify(error="not_found"), 404
    return jsonify(serialize(uid, u))


@bp.post("/users")
def create_user():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="invalid_json", message="Body phải là JSON object"), 400

    errors = {}
    for field in REQUIRED:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors[field] = "required, non-empty string"
    if "email" not in errors and "@" not in data["email"]:
        errors["email"] = "invalid email"
    if errors:
        return jsonify(error="validation_failed", fields=errors), 422

    if db.email_exists(data["email"]):
        return jsonify(error="conflict", message="email đã tồn tại"), 409

    uid = db.create_user(data["first_name"].strip(),
                         data["last_name"].strip(),
                         data["email"].strip())
    location = url_for("v2.get_user", uid=uid)
    return jsonify(serialize(uid, db.get_user(uid))), 201, {"Location": location}