from flask import Flask, jsonify, request
from uuid import uuid4
app = Flask(__name__)
STUDENTS = []
@app.route("/students", methods=["POST"])
def create_student():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not name:
        return jsonify({"error":"name là bắt buộc"}), 400
    student = {
        "id": str(uuid4()),
        "name": name,
        "gpa": body.get("gpa", 0.0),
    }
    STUDENTS.append(student)
    return jsonify({"id": student["id"], "name": student["name"], "gpa": student["gpa"]}), 201

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)