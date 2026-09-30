from flask import Flask, jsonify

from errors import ApiProblem, _problem

app = Flask(__name__)

USERS = [
    {
        "id": 1,
        "name": "Dung"
    },
    {
        "id": 2,
        "name": "An"
    }
]

@app.get("/resources/<int:id>")
def get_resource(id):
    user = next(
        (u for u in USERS if u["id"] == id),
        None
    )

    if not user:
        raise ApiProblem(
            status=404,
            title="Resource Not Found",
            detail=f"Resource {id} was not found.",
            type_path="resource-not-found"
        )

    return jsonify(user)

@app.errorhandler(ApiProblem)
def handle_api_problem(error):
    return _problem(
        error.status,
        error.title,
        error.detail,
        error.type.replace(
            "https://api.example.com/problems/",
            ""
        ),
        **error.extra
    )

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception("Unexpected server error")

    return _problem(
        500,
        "Internal Server Error",
        "An unexpected error occurred."
    )

@app.route("/test-error")
def test_error():
    x = 1 / 0
    return jsonify({"result": x})

if __name__ == "__main__":
    app.run(debug=True)