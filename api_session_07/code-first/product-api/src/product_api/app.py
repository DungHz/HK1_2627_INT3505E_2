from flask import Flask

from .extensions import api
from .routes import blp


def create_app():
    app = Flask(__name__)

    app.config["API_TITLE"] = "Product API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"

    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    api.init_app(app)
    api.register_blueprint(blp)

    return app