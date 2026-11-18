from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from blueprints.v1 import bp as v1_bp
from blueprints.v2 import bp as v2_bp


def create_app(config=None):
    app = Flask(__name__)
    app.json.ensure_ascii = False          # trả tiếng Việt không bị escape \uXXXX
    if config:
        app.config.update(config)

    app.register_blueprint(v1_bp, url_prefix="/api/v1")
    app.register_blueprint(v2_bp, url_prefix="/api/v2")

    @app.after_request
    def tag_version(resp):
        # Đo adoption theo version ngay từ đầu (Tổng kết #09)
        if request.blueprint in ("v1", "v2"):
            resp.headers["X-API-Version-Served"] = request.blueprint
        return resp

    @app.errorhandler(HTTPException)
    def json_errors(e):
        return jsonify(error=e.name.lower().replace(" ", "_")), e.code

    @app.get("/api/openapi.yaml")
    def openapi():
        return send_from_directory(app.root_path, "openapi.yaml",
                                   mimetype="application/yaml")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)