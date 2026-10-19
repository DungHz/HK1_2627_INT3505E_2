from flask import Flask

from models import db, Book
from routes.books import bp


def create_app(test_config=None):
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bookstore.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

        # Seed sample data only when database is empty
        if not db.session.query(Book).first():
            seed_books()

    return app


def seed_books():
    books = [
        Book(
            title="The Great Gatsby",
            isbn="9780743273565",
            genre="Fiction",
            price_vnd=250000,
            stock=10
        ),
        Book(
            title="To Kill a Mockingbird",
            isbn="9780061120084",
            genre="Fiction",
            price_vnd=280000,
            stock=8
        ),
        Book(
            title="A Brief History of Time",
            isbn="9780553380163",
            genre="Science",
            price_vnd=320000,
            stock=6
        ),
        Book(
            title="Cosmos",
            isbn="9780345539434",
            genre="Science",
            price_vnd=400000,
            stock=9
        ),
        Book(
            title="Sapiens",
            isbn="9780062316097",
            genre="History",
            price_vnd=350000,
            stock=5
        ),
        Book(
            title="Guns, Germs, and Steel",
            isbn="9780393354324",
            genre="History",
            price_vnd=420000,
            stock=12
        ),
        Book(
            title="The Pragmatic Programmer",
            isbn="9780135957059",
            genre="Technology",
            price_vnd=550000,
            stock=7
        ),
        Book(
            title="Artificial Intelligence: A Modern Approach",
            isbn="9780134610993",
            genre="Technology",
            price_vnd=750000,
            stock=4
        ),
        Book(
            title="Charlotte's Web",
            isbn="9780064400558",
            genre="Children",
            price_vnd=180000,
            stock=15
        ),
        Book(
            title="The Little Prince",
            isbn="9780156012195",
            genre="Children",
            price_vnd=150000,
            stock=20
        )
    ]

    db.session.add_all(books)
    db.session.commit()


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)