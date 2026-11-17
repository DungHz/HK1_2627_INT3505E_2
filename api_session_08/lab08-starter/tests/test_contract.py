"""Lab 2 — kiểm chứng response thật của Flask khớp với openapi.yaml."""
import pytest
from jsonschema import validate

from tools import get_book_schema
import yaml
from pathlib import Path


def _nullable(node):
    if isinstance(node, dict):
        node = {k: _nullable(v) for k, v in node.items()}
        if node.pop("nullable", False) and isinstance(node.get("type"), str):
            node["type"] = [node["type"], "null"]
        return node
    if isinstance(node, list):
        return [_nullable(i) for i in node]
    return node


SPEC = yaml.safe_load((Path(__file__).parent.parent / "openapi.yaml").read_text(encoding="utf-8"))
BOOK = _nullable(get_book_schema())
ERROR = _nullable(SPEC["components"]["schemas"]["Error"])
PAYLOAD = {"title": "DDIA", "author": "Kleppmann", "year": 2017, "isbn": "9781449373320"}


def test_post_get_put_list_match_book_schema(client):
    created = client.post("/books", json=PAYLOAD)
    assert created.status_code == 201
    validate(created.get_json(), BOOK)
    book_id = created.get_json()["id"]

    validate(client.get(f"/books/{book_id}").get_json(), BOOK)
    validate(client.put(f"/books/{book_id}", json={"title": "T", "author": "A"}).get_json(), BOOK)
    for item in client.get("/books").get_json():
        validate(item, BOOK)


@pytest.mark.parametrize("method, url, body, status", [
    ("get", "/books/9999", None, 404),
    ("get", "/books/abc", None, 400),
    ("delete", "/books/9999", None, 404),
    ("post", "/books", {"author": "X"}, 400),
    ("get", "/books?page=0", None, 400),
])
def test_error_responses_match_error_schema(client, method, url, body, status):
    response = getattr(client, method)(url, json=body)
    assert response.status_code == status
    validate(response.get_json(), ERROR)


def test_delete_204_has_no_body_as_declared(client):
    book_id = client.post("/books", json={"title": "T", "author": "A"}).get_json()["id"]
    response = client.delete(f"/books/{book_id}")
    assert response.status_code == 204
    assert response.data == b""
