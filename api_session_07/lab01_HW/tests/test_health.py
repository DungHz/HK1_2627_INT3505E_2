def test_liveness_and_readiness_are_separate(client):
    liveness = client.get("/healthz")
    readiness = client.get("/ready")

    assert liveness.status_code == 200
    assert liveness.json == {"status": "ok"}
    assert readiness.status_code == 200
    assert readiness.json["checks"]["db"] == "ok"
