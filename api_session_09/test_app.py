from datetime import datetime, timezone
import pytest
from app import create_app


@pytest.fixture
def client():
    return create_app({"TESTING": True}).test_client()


def test_v1_shape_and_deprecation_headers(client):
    r = client.get("/api/v1/users/1")
    assert r.status_code == 200
    assert r.json == {"id": 1, "full_name": "Văn Nguyễn", "email": "a@vnu.vn"}
    assert r.headers["Sunset"] == "Mon, 31 May 2027 23:59:59 GMT"
    assert r.headers["Deprecation"].startswith("@")
    assert 'rel="successor-version"' in r.headers["Link"]
    assert r.headers["X-API-Version-Served"] == "v1"


def test_v2_shape_no_sunset(client):
    r = client.get("/api/v2/users/1")
    assert r.json == {"id": 1, "first_name": "Văn",
                      "last_name": "Nguyễn", "email": "a@vnu.vn"}
    assert "Sunset" not in r.headers


def test_not_found_is_json(client):
    assert client.get("/api/v2/users/999").status_code == 404
    assert client.get("/api/v3/users/1").json["error"] == "not_found"


def test_v2_post_then_visible_in_v1(client):
    r = client.post("/api/v2/users", json={
        "first_name": "Minh", "last_name": "Lê", "email": "minh@vnu.vn"})
    assert r.status_code == 201
    uid = r.json["id"]
    assert r.headers["Location"] == f"/api/v2/users/{uid}"
    # Cùng data source -> v1 vẫn đọc được, theo shape cũ
    assert client.get(f"/api/v1/users/{uid}").json["full_name"] == "Minh Lê"


@pytest.mark.parametrize("body,code", [
    ({"first_name": "A"}, 422),
    ({"first_name": "A", "last_name": "B", "email": "khong-hop-le"}, 422),
    ({"first_name": "A", "last_name": "B", "email": "a@vnu.vn"}, 409),
])
def test_v2_post_validation(client, body, code):
    assert client.post("/api/v2/users", json=body).status_code == code


def test_v2_post_non_json(client):
    r = client.post("/api/v2/users", data="x", content_type="text/plain")
    assert r.status_code == 400


def test_v1_gone_after_sunset():
    past = datetime(2020, 1, 1, tzinfo=timezone.utc)
    c = create_app({"TESTING": True, "V1_SUNSET": past}).test_client()
    r = c.get("/api/v1/users/1")
    assert r.status_code == 410
    assert r.json["use_instead"] == "/api/v2/users"