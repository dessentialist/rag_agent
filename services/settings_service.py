import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from database import db
from models import Setting


logger = logging.getLogger(__name__)


class SettingsValidationError(Exception):
    """Raised when settings fail validation."""


def _get_setting(key: str) -> Optional[Dict[str, Any]]:
    """Fetch a settings record by key.

    Returns the value JSON dict or None if not present.
    """
    record = Setting.query.get(key)
    return record.value if record else None


def _set_setting(key: str, value: Dict[str, Any]) -> None:
    """Create or update a settings record with validation and timestamp."""
    if not isinstance(value, dict):
        raise SettingsValidationError("Settings value must be a JSON object (dict)")

    record = Setting.query.get(key)
    if record is None:
        record = Setting(key=key, value=value, updated_at=datetime.utcnow())
        db.session.add(record)
    else:
        record.value = value
        record.updated_at = datetime.utcnow()
    db.session.commit()
    logger.info(f"Saved settings for key='{key}'")


def _validate_hex_color(color: str) -> bool:
    return isinstance(color, str) and bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", color))


def ensure_default_ui_settings() -> None:
    """Seed neutral, non-sensitive UI settings if missing.

    This creates 'general', 'theme', and 'ui' groups with neutral defaults so the
    app renders without branding. No API keys or model parameters are seeded here.
    """
    general = _get_setting("general") or {}
    theme = _get_setting("theme") or {}
    ui = _get_setting("ui") or {}

    changed = False

    if not general:
        general = {
            "brand_name": "RAG Agent",
            "logo_url": None,
        }
        _set_setting("general", general)
        changed = True

    if not theme:
        theme = {
            "primary": "#7aa2f7",
            "secondary": "#6c757d",
            "success": "#28a745",
            "danger": "#dc3545",
            "warning": "#ffc107",
            "info": "#17a2b8",
            "light": "#f8f9fa",
            "dark": "#343a40",
            "text_dark": "#212529",
            "text_light": "#f8f9fa",
            "text_muted": "#6c757d",
            "border": "#dee2e6",
        }
        _set_setting("theme", theme)
        changed = True

    if not ui:
        ui = {
            "welcome_message": "Hi! I'm your local RAG assistant. Ask me anything about your knowledge base.",
            "predefined_prompts": [
                {"title": "What can you do?", "description": "What types of questions can I ask?"},
                {"title": "Search docs", "description": "Find info about data sources"},
                {"title": "Troubleshoot", "description": "Why isn't my index returning results?"},
            ],
            "default_course_thumbnail": "/static/images/course_thumbnail.svg",
        }
        _set_setting("ui", ui)
        changed = True

    if changed:
        logger.info("Seeded default UI settings (general/theme/ui)")


# Typed getters/setters

def get_general_settings() -> Dict[str, Any]:
    value = _get_setting("general") or {}
    brand_name = value.get("brand_name") or "RAG Agent"
    logo_url = value.get("logo_url")
    return {"brand_name": brand_name, "logo_url": logo_url}


def set_general_settings(brand_name: str, logo_url: Optional[str]) -> None:
    if not brand_name or not isinstance(brand_name, str):
        raise SettingsValidationError("brand_name must be a non-empty string")
    _set_setting("general", {"brand_name": brand_name, "logo_url": logo_url})


def get_theme_settings() -> Dict[str, str]:
    theme = _get_setting("theme") or {}
    return theme


def set_theme_settings(theme: Dict[str, str]) -> None:
    for key, val in theme.items():
        if not _validate_hex_color(val):
            raise SettingsValidationError(f"Invalid color for '{key}': {val}")
    _set_setting("theme", theme)


def get_ui_settings() -> Dict[str, Any]:
    return _get_setting("ui") or {}


def set_ui_settings(welcome_message: str, predefined_prompts: List[Dict[str, str]], default_course_thumbnail: Optional[str]) -> None:
    if not isinstance(predefined_prompts, list):
        raise SettingsValidationError("predefined_prompts must be a list")
    _set_setting("ui", {
        "welcome_message": welcome_message,
        "predefined_prompts": predefined_prompts,
        "default_course_thumbnail": default_course_thumbnail,
    })


def get_openai_settings() -> Dict[str, Any]:
    return _get_setting("openai") or {}


def set_openai_settings(api_key: str, llm_model: str, temperature: float, max_tokens: int, response_format: Optional[str] = None) -> None:
    if not api_key:
        raise SettingsValidationError("OpenAI api_key is required")
    if not llm_model:
        raise SettingsValidationError("OpenAI llm_model is required")
    if temperature is None or not (0.0 <= float(temperature) <= 2.0):
        raise SettingsValidationError("temperature must be between 0.0 and 2.0")
    if max_tokens is None or int(max_tokens) <= 0:
        raise SettingsValidationError("max_tokens must be a positive integer")
    _set_setting("openai", {
        "api_key": api_key,
        "llm_model": llm_model,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "response_format": response_format or "json_object",
    })


def get_embedding_settings() -> Dict[str, Any]:
    return _get_setting("embedding") or {}


def set_embedding_settings(embedding_model: str) -> None:
    if not embedding_model:
        raise SettingsValidationError("embedding_model is required")
    _set_setting("embedding", {"embedding_model": embedding_model})


def get_pinecone_settings() -> Dict[str, Any]:
    return _get_setting("pinecone") or {}


def set_pinecone_settings(api_key: str, index_name: str, dimension: int, metric: str, cloud: str, region: str, search_limit: int = 5) -> None:
    if not api_key:
        raise SettingsValidationError("Pinecone api_key is required")
    if not index_name:
        raise SettingsValidationError("Pinecone index_name is required")
    if int(dimension) <= 0:
        raise SettingsValidationError("Pinecone dimension must be positive")
    if metric not in {"cosine", "dotproduct", "euclidean"}:
        raise SettingsValidationError("Pinecone metric must be one of 'cosine', 'dotproduct', 'euclidean'")
    _set_setting("pinecone", {
        "api_key": api_key,
        "index_name": index_name,
        "dimension": int(dimension),
        "metric": metric,
        "cloud": cloud,
        "region": region,
        "search_limit": int(search_limit),
    })


def get_rag_settings() -> Dict[str, Any]:
    return _get_setting("rag") or {}


def set_rag_settings(chunk_size: int, chunk_overlap: int, allowed_extensions: List[str]) -> None:
    if int(chunk_size) <= 0:
        raise SettingsValidationError("chunk_size must be positive")
    if int(chunk_overlap) < 0:
        raise SettingsValidationError("chunk_overlap must be >= 0")
    if not isinstance(allowed_extensions, list) or not all(isinstance(ext, str) for ext in allowed_extensions):
        raise SettingsValidationError("allowed_extensions must be a list of strings")
    _set_setting("rag", {
        "chunk_size": int(chunk_size),
        "chunk_overlap": int(chunk_overlap),
        "allowed_extensions": allowed_extensions,
    })


def readiness() -> Dict[str, Any]:
    """Compute application readiness and missing required settings.

    Required for ready=True:
      - openai.api_key
      - openai.llm_model
      - embedding.embedding_model
      - pinecone.api_key
      - pinecone.index_name
      - pinecone.dimension
    """
    missing: List[str] = []

    openai_cfg = get_openai_settings()
    if not openai_cfg.get("api_key"):
        missing.append("openai.api_key")
    if not openai_cfg.get("llm_model"):
        missing.append("openai.llm_model")

    embedding_cfg = get_embedding_settings()
    if not embedding_cfg.get("embedding_model"):
        missing.append("embedding.embedding_model")

    pinecone_cfg = get_pinecone_settings()
    if not pinecone_cfg.get("api_key"):
        missing.append("pinecone.api_key")
    if not pinecone_cfg.get("index_name"):
        missing.append("pinecone.index_name")
    if not pinecone_cfg.get("dimension"):
        missing.append("pinecone.dimension")

    ready = len(missing) == 0
    return {"ready": ready, "missing_keys": missing}


