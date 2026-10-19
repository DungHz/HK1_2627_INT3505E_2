from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, ForeignKey, Table, Column
from sqlalchemy.orm import mapped_column, relationship

db = SQLAlchemy()


# Association table: Book N:M Author
book_authors = Table(
    "book_authors",
    db.metadata,
    Column("book_id", ForeignKey("book.id"), primary_key=True),
    Column("author_id", ForeignKey("author.id"), primary_key=True)
)


class Book(db.Model):
    id = mapped_column(Integer, primary_key=True)
    title = mapped_column(String(200))
    isbn = mapped_column(String(13), unique=True)
    price_vnd = mapped_column(Integer)
    stock = mapped_column(Integer, default=0)

    category_id = mapped_column(ForeignKey("category.id"))

    category = relationship(
        "Category",
        back_populates="books"
    )

    authors = relationship(
        "Author",
        secondary=book_authors,
        back_populates="books"
    )

    reviews = relationship(
        "Review",
        back_populates="book"
    )

    def to_dict(self):
        return {
            "id": f"book_{self.id}",
            "title": self.title,
            "isbn": self.isbn,
            "price_vnd": self.price_vnd,
            "stock": self.stock,
            "category": self.category.name if self.category else None
        }


class Author(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100))
    bio = mapped_column(Text)

    books = relationship(
        "Book",
        secondary=book_authors,
        back_populates="authors"
    )


class Category(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), unique=True)

    books = relationship(
        "Book",
        back_populates="category"
    )


class User(db.Model):
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100))
    email = mapped_column(String(255), unique=True)

    reviews = relationship(
        "Review",
        back_populates="user"
    )


class Review(db.Model):
    id = mapped_column(Integer, primary_key=True)
    rating = mapped_column(Integer)
    comment = mapped_column(Text)

    book_id = mapped_column(ForeignKey("book.id"))
    user_id = mapped_column(ForeignKey("user.id"))

    book = relationship(
        "Book",
        back_populates="reviews"
    )

    user = relationship(
        "User",
        back_populates="reviews"
    )