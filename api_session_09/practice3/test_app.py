import logging
from datetime import datetime, timedelta, timezone

import pytest
from flask import Flask

import sunset
from app import V1_SUNSET, app


@pytest.fixture
def client():
    app.testing = True
    return app.test_client()


def freeze_time(monkeypatch, dt):
    """Giả lập 'bây giờ' là dt."""
    monkeypatch.setattr(sunset, "_now", lambda: dt)


def test_before_sunset_returns_200_with_headers(client, monkeypatch):
    freeze_time(monkeypatch, V1_SUNSET - timedelta(days=30))
    r = client.get("/api/v1/users/1")
    assert r.status_code == 200
    assert r.get_json() == {"id": 1, "full_name": "Văn Nguyễn"}
    assert r.headers["Sunset"] == sunset.http_date(V1_SUNSET)
    assert r.headers["Deprecation"] == "true"
    assert r.headers["Link"] == '</api/v2/users/1>; rel="successor-version"'


def test_exactly_at_sunset_returns_410(client, monkeypatch):
    freeze_time(monkeypatch, V1_SUNSET)
    assert client.get("/api/v1/users/1").status_code == 410


def test_after_sunset_returns_410_with_successor(client, monkeypatch):
    freeze_time(monkeypatch, V1_SUNSET + timedelta(seconds=1))
    r = client.get("/api/v1/users/2")
    assert r.status_code == 410
    body = r.get_json()
    assert body["error"] == "gone"
    assert body["use_instead"] == "/api/v2/users/2"
    assert r.headers["Sunset"] == sunset.http_date(V1_SUNSET)
    assert "successor-version" in r.headers["Link"]


def test_not_found_still_has_deprecation_headers(client, monkeypatch):
    freeze_time(monkeypatch, V1_SUNSET - timedelta(days=1))
    r = client.get("/api/v1/users/999")
    assert r.status_code == 404
    assert "Sunset" in r.headers


def test_v2_is_not_deprecated(client):
    r = client.get("/api/v2/users/1")
    assert r.status_code == 200
    assert "Sunset" not in r.headers
    assert "Deprecation" not in r.headers


def test_deprecated_call_is_logged(client, monkeypatch, caplog):
    freeze_time(monkeypatch, V1_SUNSET - timedelta(days=1))
    with caplog.at_level(logging.WARNING, logger="sunset"):
        client.get("/api/v1/users/1")
    assert "deprecated_call path=/api/v1/users/1" in caplog.text


def test_http_date_format():
    dt = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    assert sunset.http_date(dt) == "Thu, 31 Dec 2026 23:59:59 GMT"


def test_naive_datetime_is_rejected():
    with pytest.raises(ValueError):
        sunset.deprecate_at(datetime(2026, 12, 31))


def test_deprecated_since_uses_rfc9745_format():
    demo = Flask("demo")
    since = datetime(2026, 7, 1, tzinfo=timezone.utc)

    @demo.route("/x")
    @sunset.deprecate_at(datetime(2099, 1, 1, tzinfo=timezone.utc),
                         deprecated_since=since)
    def x():
        return {"ok": True}

    r = demo.test_client().get("/x")
    assert r.headers["Deprecation"] == "@1782864000"