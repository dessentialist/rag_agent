import logging

from flask import Blueprint, jsonify, request
from database import db
from openai import OpenAI

from services.agent_registry import (
    create_agent as registry_create_agent,
)
from services.agent_registry import (
    delete_agent as registry_delete_agent,
)
from services.agent_registry import (
    list_agents,
)
from services.agent_registry import (
    update_agent as registry_update_agent,
)
from services.pinecone_service import initialize_pinecone
from services.settings_service import (
    SettingsValidationError,
    ensure_default_ui_settings,
    get_embedding_settings,
    get_general_settings,
    get_openai_settings,
    get_pinecone_settings,
    get_rag_settings,
    get_theme_settings,
    get_ui_settings,
    readiness,
    set_embedding_settings,
    set_general_settings,
    set_openai_settings,
    set_pinecone_settings,
    set_rag_settings,
    set_theme_settings,
    set_ui_settings,
)

logger = logging.getLogger(__name__)


settings_bp = Blueprint("settings_bp", __name__, url_prefix="/api")


@settings_bp.route("/health", methods=["GET"])
def health():
    """Readiness probe for the application.

    Returns 200 with JSON including readiness state and any missing keys.
    Note: This endpoint is safe to call before the app is fully configured.
    """
    try:
        # Seed minimal UI settings so templates can render neutrally
        ensure_default_ui_settings()

        status = readiness()
        response = {
            "status": "ok",
            "ready": status["ready"],
            "missing_keys": status["missing_keys"],
        }
        http_code = 200
        return jsonify(response), http_code
    except Exception as exc:
        logger.error(f"/health error: {exc}", exc_info=True)
        return jsonify({"status": "error"}), 500


# --- Minimal Agent CRUD APIs (Chunk 3 requirement) ---


@settings_bp.route("/agents", methods=["GET"])
def get_agents():
    """List all configured agents with their selection rules.

    This endpoint returns non-secret agent configuration. Intended for admin UI.
    """
    try:
        agents = list_agents()
        result = []
        for a in agents:
            result.append(
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "role_system_prompt": a.role_system_prompt,
                    "llm_model": a.llm_model,
                    "temperature": a.temperature,
                    "max_tokens": a.max_tokens,
                    "response_format": a.response_format,
                    "selection_rules": a.selection_rules,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                    "updated_at": a.updated_at.isoformat() if a.updated_at else None,
                }
            )
        return jsonify({"agents": result}), 200
    except Exception as exc:
        logger.error(f"GET /agents error: {exc}", exc_info=True)
        return jsonify({"error": "Could not list agents"}), 500


@settings_bp.route("/agents", methods=["POST"])
def create_agent():
    """Create a new agent.

    Expects JSON with keys: name, description (opt), role_system_prompt, llm_model,
    temperature, max_tokens, response_format (opt), selection_rules (JSON).
    """
    try:
        payload = request.get_json(force=True) or {}
        agent = registry_create_agent(
            name=payload.get("name"),
            description=payload.get("description"),
            role_system_prompt=payload.get("role_system_prompt"),
            llm_model=payload.get("llm_model"),
            temperature=payload.get("temperature", 0.3),
            max_tokens=payload.get("max_tokens", 1200),
            response_format=payload.get("response_format", "json_object"),
            selection_rules=payload.get("selection_rules") or {},
        )
        return jsonify({"id": agent.id}), 201
    except Exception as exc:
        db.session.rollback()
        logger.error(f"POST /agents error: {exc}", exc_info=True)
        return jsonify({"error": "Could not create agent"}), 400


@settings_bp.route("/agents/<int:agent_id>", methods=["PUT"])
def update_agent(agent_id: int):
    """Update fields on an existing agent. Accepts partial JSON."""
    try:
        payload = request.get_json(force=True) or {}
        agent = registry_update_agent(agent_id, **payload)
        if agent is None:
            return jsonify({"error": "Agent not found"}), 404
        return jsonify({"success": True}), 200
    except Exception as exc:
        db.session.rollback()
        logger.error(f"PUT /agents/{agent_id} error: {exc}", exc_info=True)
        return jsonify({"error": "Could not update agent"}), 400


@settings_bp.route("/agents/<int:agent_id>", methods=["DELETE"])
def delete_agent(agent_id: int):
    """Delete an agent by id."""
    try:
        ok = registry_delete_agent(agent_id)
        if not ok:
            return jsonify({"error": "Agent not found"}), 404
        return jsonify({"success": True}), 200
    except Exception as exc:
        db.session.rollback()
        logger.error(f"DELETE /agents/{agent_id} error: {exc}", exc_info=True)
        return jsonify({"error": "Could not delete agent"}), 400


@settings_bp.route("/settings", methods=["GET"])
def get_all_settings():
    try:
        data = {
            "general": get_general_settings(),
            "theme": get_theme_settings(),
            "ui": get_ui_settings(),
            "openai": get_openai_settings(),
            "embedding": get_embedding_settings(),
            "pinecone": get_pinecone_settings(),
            "rag": get_rag_settings(),
        }
        return jsonify(data)
    except Exception as exc:
        logger.error(f"/settings GET error: {exc}", exc_info=True)
        return jsonify({"error": "Failed to fetch settings"}), 500


@settings_bp.route("/settings/general", methods=["POST"])
def update_general_settings():
    body = request.json or {}
    try:
        set_general_settings(body.get("brand_name"), body.get("logo_url"))
        return jsonify({"success": True, "general": get_general_settings()})
    except SettingsValidationError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as exc:
        logger.error(f"update_general_settings error: {exc}", exc_info=True)
        return jsonify({"error": "Failed to update general settings"}), 500


@settings_bp.route("/settings/theme", methods=["POST"])
def update_theme_settings():
    body = request.json or {}
    try:
        set_theme_settings(body)
        return jsonify({"success": True, "theme": get_theme_settings()})
    except SettingsValidationError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as exc:
        logger.error(f"update_theme_settings error: {exc}", exc_info=True)
        return jsonify({"error": "Failed to update theme settings"}), 500


@settings_bp.route("/settings/ui", methods=["POST"])
def update_ui_settings():
    body = request.json or {}
    try:
        set_ui_settings(
            body.get("welcome_message", ""),
            body.get("predefined_prompts", []),
            body.get("default_course_thumbnail"),
        )
        return jsonify({"success": True, "ui": get_ui_settings()})
    except SettingsValidationError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as exc:
        logger.error(f"update_ui_settings error: {exc}", exc_info=True)
        return jsonify({"error": "Failed to update UI settings"}), 500


@settings_bp.route("/settings/openai", methods=["POST"])
def update_openai_settings():
    body = request.json or {}
    try:
        set_openai_settings(
            api_key=body.get("api_key"),
            llm_model=body.get("llm_model"),
            temperature=body.get("temperature", 0.3),
            max_tokens=body.get("max_tokens", 1000),
            response_format=body.get("response_format", "json_object"),
        )
        return jsonify({"success": True, "openai": get_openai_settings()})
    except SettingsValidationError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as exc:
        logger.error(f"update_openai_settings error: {exc}", exc_info=True)
        return jsonify({"error": "Failed to update OpenAI settings"}), 500


@settings_bp.route("/settings/embedding", methods=["POST"])
def update_embedding_settings():
    body = request.json or {}
    try:
        set_embedding_settings(body.get("embedding_model"))
        return jsonify({"success": True, "embedding": get_embedding_settings()})
    except SettingsValidationError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as exc:
        logger.error(f"update_embedding_settings error: {exc}", exc_info=True)
        return jsonify({"error": "Failed to update embedding settings"}), 500


@settings_bp.route("/settings/pinecone", methods=["POST"])
def update_pinecone_settings():
    body = request.json or {}
    try:
        set_pinecone_settings(
            api_key=body.get("api_key"),
            index_name=body.get("index_name"),
            dimension=int(body.get("dimension")),
            metric=body.get("metric", "cosine"),
            cloud=body.get("cloud", "aws"),
            region=body.get("region", "us-west-2"),
            search_limit=int(body.get("search_limit", 5)),
        )
        return jsonify({"success": True, "pinecone": get_pinecone_settings()})
    except SettingsValidationError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as exc:
        logger.error(f"update_pinecone_settings error: {exc}", exc_info=True)
        return jsonify({"error": "Failed to update Pinecone settings"}), 500


@settings_bp.route("/settings/rag", methods=["POST"])
def update_rag_settings():
    body = request.json or {}
    try:
        allowed = body.get("allowed_extensions") or [
            "txt",
            "json",
            "md",
            "jsonl",
            "csv",
            "docx",
            "pdf",
            "xlsx",
        ]
        set_rag_settings(
            chunk_size=int(body.get("chunk_size", 500)),
            chunk_overlap=int(body.get("chunk_overlap", 30)),
            allowed_extensions=allowed,
        )
        return jsonify({"success": True, "rag": get_rag_settings()})
    except SettingsValidationError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as exc:
        logger.error(f"update_rag_settings error: {exc}", exc_info=True)
        return jsonify({"error": "Failed to update RAG settings"}), 500


@settings_bp.route("/settings/test/openai", methods=["POST"])
def test_openai():
    try:
        cfg = get_openai_settings()
        api_key = cfg.get("api_key")
        if not api_key:
            return jsonify({"ok": False, "error": "OpenAI API key is missing"}), 400
        client = OpenAI(api_key=api_key)
        _ = client.models.list()
        return jsonify({"ok": True})
    except Exception as exc:
        logger.error(f"OpenAI test failed: {exc}", exc_info=True)
        return jsonify({"ok": False, "error": str(exc)}), 500


@settings_bp.route("/settings/test/pinecone", methods=["POST"])
def test_pinecone():
    try:
        initialize_pinecone()
        return jsonify({"ok": True})
    except Exception as exc:
        logger.error(f"Pinecone test failed: {exc}", exc_info=True)
        return jsonify({"ok": False, "error": str(exc)}), 500


@settings_bp.route("/diagnostics", methods=["GET"])
def diagnostics():
    report = {"ready": False, "missing_keys": [], "openai": {}, "pinecone": {}, "db": {}}
    try:
        status = readiness()
        report["ready"] = status.get("ready", False)
        report["missing_keys"] = status.get("missing_keys", [])
    except Exception as exc:
        report["readiness_error"] = str(exc)

    try:
        cfg = get_openai_settings()
        api_key = cfg.get("api_key")
        if api_key:
            client = OpenAI(api_key=api_key)
            _ = client.models.list()
            report["openai"] = {"ok": True}
        else:
            report["openai"] = {"ok": False, "error": "missing api_key"}
    except Exception as exc:
        report["openai"] = {"ok": False, "error": str(exc)}

    try:
        initialize_pinecone()
        report["pinecone"] = {"ok": True}
    except Exception as exc:
        report["pinecone"] = {"ok": False, "error": str(exc)}

    report["db"] = {"ok": True}
    return jsonify(report)
