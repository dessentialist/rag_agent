import logging
from flask import Blueprint, jsonify
from services.settings_service import readiness, ensure_default_ui_settings


logger = logging.getLogger(__name__)


settings_bp = Blueprint('settings_bp', __name__, url_prefix='/api')


@settings_bp.route('/health', methods=['GET'])
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


