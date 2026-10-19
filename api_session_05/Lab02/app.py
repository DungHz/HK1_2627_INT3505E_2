from flask import Flask

from models import db, Book, Category
from routes.books import bp


def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookstore.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

        # Seed sample data only when database is empty
        if not db.session.query(Book).first():

            programming = Category(
                name="Programming"
            )

            database = Category(
                name="Database"
            )

            db.session.add_all([
                programming,
                database
            ])

            db.session.flush()

            books = [
                Book(
                    title="Clean Code",
                    isbn="9780132350884",
                    price_vnd=450000,
                    stock=10,
                    category_id=programming.id
                ),
                Book(
                    title="Design Patterns",
                    isbn="9780201633610",
                    price_vnd=520000,
                    stock=8,
                    category_id=programming.id
                ),
            ]

            db.session.add_all(books)
            db.session.commit()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)