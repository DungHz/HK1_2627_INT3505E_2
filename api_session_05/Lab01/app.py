from flask import Flask, jsonify
from models import db
from routes.books import books_bp


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookstore.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(books_bp, url_prefix="/api/v1/books")

    @app.get("/")
    def home():
        return jsonify({"message": "Bookstore API", "books": "/api/v1/books"})

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
