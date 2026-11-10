"""Flask application factory."""

import os

from flask import Flask

from .api import health_bp, orders_bp, products_bp
from .errors import register_error_handlers
from .extensions import db, migrate
from . import models  # noqa: F401 - make model metadata available to Alembic


def create_app(config=None) -> Flask:
    app = Flask(__name__)

    if isinstance(config, dict):
        app.config.from_object("product_api.config.DefaultConfig")
        app.config.from_mapping(config)
    else:
        config_object = config or os.environ.get(
            "APP_CONFIG", "product_api.config.DefaultConfig"
        )
        app.config.from_object(config_object)

    os.makedirs(app.instance_path, exist_ok=True)
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(health_bp)
    register_error_handlers(app)

    return app
