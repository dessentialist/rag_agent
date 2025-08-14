import json


def test_agents_crud_flow(test_app_client):
    # List agents (may be seeded or empty)
    resp = test_app_client.get("/api/agents")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "agents" in data

    # Create new agent
    payload = {
        "name": "documentation",
        "description": "Docs agent",
        "role_system_prompt": "Be terse and precise.",
        "llm_model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 800,
        "response_format": "json_object",
        "selection_rules": {"doc_type_any_of": ["documentation"]},
    }
    resp = test_app_client.post(
        "/api/agents", data=json.dumps(payload), content_type="application/json"
    )
    assert resp.status_code in (201, 400)  # 201 when unique, 400 if duplicate
    if resp.status_code == 201:
        agent_id = resp.get_json()["id"]
        # Update
        resp = test_app_client.put(
            f"/api/agents/{agent_id}",
            data=json.dumps({"description": "Updated"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        # Delete
        resp = test_app_client.delete(f"/api/agents/{agent_id}")
        assert resp.status_code == 200
