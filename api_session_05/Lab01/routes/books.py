import json
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy.exc import IntegrityError

from models import Book, Category, db

books_bp = Blueprint("books", __name__)


def load_book_schema():
    schema_path = Path(current_app.root_path) / "schemas" / "book.json"
    with schema_path.open("r", encoding="utf-8") as schema_file:
        return json.load(schema_file)


def validate_book(data):
    """Small schema-based validation for the fields accepted by this lab."""
    if not isinstance(data, dict):
        return "JSON body must be an object"

    schema = load_book_schema()
    required = schema.get("required", [])
    for field in required:
        if field not in data:
            return f"'{field}' is required"

    properties = schema["properties"]
    for field, value in data.items():
        if field not in properties and field != "category_id":
            return f"Unknown field: {field}"
        if field in properties:
            rules = properties[field]
            if rules.get("type") == "string" and value is not None and not isinstance(value, str):
                return f"'{field}' must be a string"
            if rules.get("type") == "integer" and (not isinstance(value, int) or isinstance(value, bool)):
                return f"'{field}' must be an integer"
            if rules.get("minimum") is not None and value < rules["minimum"]:
                return f"'{field}' must be at least {rules['minimum']}"
    if "category_id" in data and data["category_id"] is not None:
        if not isinstance(data["category_id"], int) or isinstance(data["category_id"], bool):
            return "'category_id' must be an integer"
        if not db.session.get(Category, data["category_id"]):
            return "category_id does not exist"
    return None


@books_bp.get("")
def get_books():
    """GET /api/v1/books?limit=20"""
    try:
        limit = int(request.args.get("limit", 100))
        if limit < 1:
            raise ValueError
    except ValueError:
        return jsonify({"error": "limit must be a positive integer"}), 400

    books = Book.query.order_by(Book.id).limit(min(limit, 100)).all()
    return jsonify([book.to_dict() for book in books]), 200


@books_bp.get("/<int:book_id>")
def get_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    return jsonify(book.to_dict()), 200


@books_bp.post("")
def create_book():
    data = request.get_json(silent=True)
    error = validate_book(data)
    if error:
        return jsonify({"error": error}), 400

    book = Book(
        title=data["title"].strip(),
        isbn=data.get("isbn"),
        price_vnd=data.get("price_vnd", 0),
        stock=data.get("stock", 0),
        category_id=data.get("category_id"),
    )
    if not book.title:
        return jsonify({"error": "'title' must not be empty"}), 400

    try:
        db.session.add(book)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "ISBN already exists"}), 409

    return jsonify(book.to_dict()), 201


@books_bp.put("/<int:book_id>")
def update_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404

    data = request.get_json(silent=True)
    error = validate_book(data)
    if error:
        return jsonify({"error": error}), 400

    for field in ("title", "isbn", "price_vnd", "stock", "category_id"):
        if field in data:
            setattr(book, field, data[field])
    if not book.title or not book.title.strip():
        return jsonify({"error": "'title' must not be empty"}), 400
    book.title = book.title.strip()

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "ISBN already exists"}), 409
    return jsonify(book.to_dict()), 200


@books_bp.delete("/<int:book_id>")
def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        return jsonify({"error": "Book not found"}), 404
    db.session.delete(book)
    db.session.commit()
    return "", 204
