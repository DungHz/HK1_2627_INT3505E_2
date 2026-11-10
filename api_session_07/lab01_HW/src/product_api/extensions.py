"""Shared Flask extensions. They are initialized by the application factory."""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate(compare_type=True)
