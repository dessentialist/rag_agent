from database import db
from models import Setting
from services.settings_service import (
    readiness,
    set_embedding_settings,
    set_openai_settings,
    set_pinecone_settings,
)


def _clear_settings():
    # Remove all settings rows to force non-ready state
    for s in Setting.query.all():
        db.session.delete(s)
    db.session.commit()


def test_readiness_missing_all(test_app_client):
    _clear_settings()
    status = readiness()
    assert status["ready"] is False
    assert "openai.api_key" in status["missing_keys"]
    assert "embedding.embedding_model" in status["missing_keys"]
    assert "pinecone.index_name" in status["missing_keys"]


def test_readiness_becomes_ready_after_settings(test_app_client):
    # Provide minimal required settings
    # Ensure no lingering failed transactions
    from database import db

    try:
        db.session.rollback()
    except Exception:
        pass
    _clear_settings()
    set_openai_settings(api_key="sk-test", llm_model="gpt-4o", temperature=0.3, max_tokens=1000)
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
    status = readiness()
    assert status["ready"] is True
    assert status["missing_keys"] == []
