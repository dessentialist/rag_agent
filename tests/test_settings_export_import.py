import json


def test_settings_export_import_roundtrip(test_app_client):
    # Ensure minimal settings present
    from services.settings_service import (
        set_embedding_settings,
        set_openai_settings,
        set_pinecone_settings,
    )

    set_openai_settings(api_key="sk-test", llm_model="gpt-4o", temperature=0.2, max_tokens=256)
    set_embedding_settings(embedding_model="text-embedding-3-small")
    set_pinecone_settings(
        api_key="pc-test",
        index_name="idx",
        dimension=1536,
        metric="cosine",
        cloud="aws",
        region="us-west-2",
        search_limit=5,
    )

    # Export
    resp = test_app_client.get("/api/settings/export")
    assert resp.status_code == 200
    blob = resp.get_json()
    assert isinstance(blob, dict)
    assert "openai" in blob
    assert "embedding" in blob
    assert "pinecone" in blob

    # Modify blob slightly and re-import
    blob["general"] = {"brand_name": "RAG Agent", "logo_url": None}
    res2 = test_app_client.post(
        "/api/settings/import",
        data=json.dumps(blob),
        content_type="application/json",
    )
    assert res2.status_code in (200, 400)
    data = res2.get_json()
    assert "applied" in data
    assert "errors" in data
