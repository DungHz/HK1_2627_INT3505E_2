import pytest

from app import app


@pytest.fixture
def client():
    app.testing = True
    return app.test_client()


def test_default_is_latest(client):
    r = client.get("/users/1")
    assert r.status_code == 200
    assert r.headers["X-API-Version-Served"] == "2"
    data = r.get_json()
    assert data["first_name"] == "Văn"
    assert data["last_name"] == "Nguyễn"
    assert "full_name" not in data


def test_v1_explicit(client):
    r = client.get("/users/1", headers={"X-API-Version": "1"})
    assert r.status_code == 200
    assert r.headers["X-API-Version-Served"] == "1"
    assert r.get_json() == {"id": 1, "full_name": "Văn Nguyễn"}


def test_dated_version_uses_v2_schema(client):
    r = client.get("/users/1", headers={"X-API-Version": "2024-06-20"})
    assert r.status_code == 200
    assert r.headers["X-API-Version-Served"] == "2024-06-20"
    assert "first_name" in r.get_json()


def test_unsupported_version_returns_400(client):
    r = client.get("/users/1", headers={"X-API-Version": "99"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "unsupported version"
    assert "X-API-Version-Served" not in r.headers


def test_empty_header_falls_back_to_default(client):
    r = client.get("/users/1", headers={"X-API-Version": ""})
    assert r.status_code == 200
    assert r.headers["X-API-Version-Served"] == "2"


def test_user_not_found_returns_404(client):
    r = client.get("/users/999", headers={"X-API-Version": "1"})
    assert r.status_code == 404
    assert r.headers["X-API-Version-Served"] == "1"


def test_vary_header_present(client):
    r = client.get("/users/1")
    assert r.headers["Vary"] == "X-API-Version"