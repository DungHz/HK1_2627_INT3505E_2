import copy

import pytest

import gateway
from app import app


@pytest.fixture(autouse=True)
def reset_config():
    """Mỗi test bắt đầu với cấu hình gốc, không ảnh hưởng lẫn nhau."""
    original = copy.deepcopy(gateway.CONFIG)
    yield
    gateway.CONFIG.clear()
    gateway.CONFIG.update(original)


@pytest.fixture
def client():
    app.testing = True
    return app.test_client()


def post_order(client, account_id, cohort=None, amount=100000):
    headers = {"X-Cohort": cohort} if cohort else {}
    return client.post("/orders", json={"account_id": account_id, "amount": amount},
                       headers=headers)


def test_cohort_beta_goes_to_v2(client):
    r = post_order(client, "any", cohort="beta")
    assert r.status_code == 201
    assert r.headers["X-Order-Handler"] == "v2"
    assert r.headers["X-Route-Reason"] == "cohort:beta"
    assert r.get_json()["amount"]["currency"] == "VND"


def test_cohort_is_case_insensitive(client):
    assert post_order(client, "any", cohort="BETA").headers["X-Order-Handler"] == "v2"


def test_allowlisted_account_goes_to_v2(client):
    gateway.CONFIG["v2_percent"] = 0
    r = post_order(client, "acct_42")
    assert r.headers["X-Order-Handler"] == "v2"
    assert r.headers["X-Route-Reason"] == "allowlist:acct_42"


def test_percent_zero_sends_ordinary_account_to_v1(client):
    gateway.CONFIG["v2_percent"] = 0
    r = post_order(client, "acct_7")
    assert r.status_code == 200
    assert r.headers["X-Order-Handler"] == "v1"
    assert "order_id" in r.get_json()


def test_percent_100_sends_everyone_to_v2(client):
    gateway.CONFIG["v2_percent"] = 100
    for i in range(50):
        assert post_order(client, f"acct_{i}").headers["X-Order-Handler"] == "v2"


def test_kill_switch_overrides_everything(client):
    gateway.CONFIG["enabled"] = False
    for acct, cohort in [("acct_42", None), ("any", "beta"), ("acct_7", None)]:
        r = post_order(client, acct, cohort=cohort)
        assert r.headers["X-Order-Handler"] == "v1"
        assert r.headers["X-Route-Reason"] == "kill_switch"


def test_routing_is_sticky_per_account():
    results = {gateway.route_to_v2("acct_123")[0] for _ in range(20)}
    assert len(results) == 1


def test_increasing_percent_never_moves_account_back_to_v1():
    accounts = [f"acct_{i}" for i in range(2000)]
    gateway.CONFIG["v2_percent"] = 5
    at_5 = {a for a in accounts if gateway.route_to_v2(a)[0]}
    gateway.CONFIG["v2_percent"] = 50
    at_50 = {a for a in accounts if gateway.route_to_v2(a)[0]}
    assert at_5 <= at_50


def test_bucket_distribution_is_roughly_even():
    n = 10_000
    v2 = sum(gateway.bucket(f"acct_{i}") < 5 for i in range(n))
    assert 0.035 < v2 / n < 0.065


def test_missing_account_id_returns_400(client):
    assert client.post("/orders", json={"amount": 1}).status_code == 400


def test_non_json_body_returns_400(client):
    r = client.post("/orders", data="account_id=acct_42")
    assert r.status_code == 400


def test_admin_can_flip_percent(client):
    r = client.post("/admin/rollout?percent=100")
    assert r.status_code == 200
    assert r.get_json()["v2_percent"] == 100
    assert post_order(client, "acct_7").headers["X-Order-Handler"] == "v2"


@pytest.mark.parametrize("query", ["percent=101", "percent=abc", "enabled=maybe"])
def test_admin_rejects_invalid_values(client, query):
    assert client.post(f"/admin/rollout?{query}").status_code == 400