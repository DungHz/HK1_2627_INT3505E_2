from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column


db = SQLAlchemy()


class Book(db.Model):
    id = mapped_column(Integer, primary_key=True)

    title = mapped_column(
        String(200),
        nullable=False
    )

    isbn = mapped_column(
        String(13),
        unique=True,
        nullable=False
    )

    genre = mapped_column(
        String(100),
        nullable=False
    )

    price_vnd = mapped_column(
        Integer,
        nullable=False
    )

    stock = mapped_column(
        Integer,
        default=0
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "isbn": self.isbn,
            "genre": self.genre,
            "price_vnd": self.price_vnd,
            "stock": self.stock
        }