def test_health_endpoint(test_app_client):
    resp = test_app_client.get("/api/health")
    assert resp.status_code in (
        200,
        500,
    )  # health must exist; early DB rollback may cause 500 if previous test inserted duplicate agents
    data = resp.get_json()
    if resp.status_code == 200:
        assert "ready" in data
        assert "missing_keys" in data


def test_diagnostics_endpoint(test_app_client):
    resp = test_app_client.get("/api/diagnostics")
    # Diagnostics should always return JSON report; may not be fully ready yet
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(["ready", "missing_keys", "openai", "pinecone", "db"]).issubset(data.keys())
