"""LAB 1 — Books API functional tests.

A. GET /books, empty database -> HTTP 200 and []
B. GET /books/9999 -> HTTP 404, JSON code == NOT_FOUND
C. POST /books with only author -> HTTP 400, errors contains title
D. POST valid book, DELETE it, GET same id -> HTTP 404
BONUS. Validate a Book response using JSON Schema; add an unknown
       field to a *copy* of the response and assert ValidationError.
"""
import copy

import pytest
from jsonschema import ValidationError, validate

from tools import get_book_schema


# ---------------------------------------------------------------- helpers
def assert_error(response, status, code):
    """Kiểm tra error response theo format {code, message} của API."""
    assert response.status_code == status
    assert response.content_type == "application/json"
    body = response.get_json()
    assert body["code"] == code
    assert isinstance(body["message"], str) and body["message"]
    return body


def openapi_to_jsonschema(node):
    """OpenAPI 3.0 dùng `nullable: true`, nhưng thư viện jsonschema không hiểu
    từ khoá này. Chuyển {type: X, nullable: true} -> {type: [X, "null"]}."""
    if isinstance(node, dict):
        node = {k: openapi_to_jsonschema(v) for k, v in node.items()}
        if node.pop("nullable", False) and isinstance(node.get("type"), str):
            node["type"] = [node["type"], "null"]
        return node
    if isinstance(node, list):
        return [openapi_to_jsonschema(item) for item in node]
    return node


# ---------------------------------------------------------------- A
def test_list_books_empty_db_returns_empty_array(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.content_type == "application/json"
    assert response.get_json() == []          # không phải None, không phải {}


# ---------------------------------------------------------------- B
def test_get_missing_book_returns_404_not_found(client):
    response = client.get("/books/9999")

    assert_error(response, 404, "NOT_FOUND")


# ---------------------------------------------------------------- C
def test_create_book_without_title_returns_400_with_title_error(client):
    response = client.post("/books", json={"author": "X"})

    body = assert_error(response, 400, "VALIDATION_ERROR")
    fields = {e["field"] for e in body.get("errors", [])}
    assert "title" in fields


# ---------------------------------------------------------------- D
def test_deleted_book_is_no_longer_found(client):
    created = client.post("/books", json={"title": "DDIA", "author": "Kleppmann"})
    assert created.status_code == 201
    book_id = created.get_json()["id"]

    # Xác nhận side-effect: sách thực sự tồn tại trước khi xoá
    assert client.get(f"/books/{book_id}").status_code == 200

    deleted = client.delete(f"/books/{book_id}")
    assert deleted.status_code == 204
    assert deleted.data == b""                # 204 không có body

    assert_error(client.get(f"/books/{book_id}"), 404, "NOT_FOUND")


# ---------------------------------------------------------------- BONUS
@pytest.fixture()
def book_schema():
    return openapi_to_jsonschema(get_book_schema())


def test_book_response_matches_schema_and_blocks_unknown_field(client, book_schema):
    created = client.post("/books", json={
        "title": "API Design Patterns",
        "author": "J.J. Geewax",
        "year": 2021,
        "isbn": "9781617295850",
    })
    assert created.status_code == 201
    book = client.get(f"/books/{created.get_json()['id']}").get_json()

    # 1) Response thật phải khớp schema
    validate(instance=book, schema=book_schema)

    # 2) Giả lập backend lộ field nhạy cảm -> schema phải chặn
    leaked = copy.deepcopy(book)
    leaked["password_hash"] = "pbkdf2:sha256:..."
    with pytest.raises(ValidationError):
        validate(instance=leaked, schema=book_schema)


def test_book_with_null_optional_fields_matches_schema(client, sample_book, book_schema):
    """sample_book không có isbn -> isbn = null vẫn phải hợp lệ."""
    book = client.get(f"/books/{sample_book}").get_json()
    assert book["isbn"] is None

    validate(instance=book, schema=book_schema)
