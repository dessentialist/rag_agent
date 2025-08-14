import json
import logging

from flask import Flask, redirect, render_template, url_for

# Import logging configuration
from config import LOG_FORMAT, LOG_LEVEL
from database import db

# Configure logging
log_level = getattr(logging, LOG_LEVEL)
logging.basicConfig(level=log_level, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)

# Import Flask settings
from config import SESSION_SECRET

# Configure Flask
app.secret_key = SESSION_SECRET

# Import configuration
from config import (
    DATABASE_POOL_PRE_PING,
    DATABASE_POOL_RECYCLE,
    DATABASE_TRACK_MODIFICATIONS,
    # Database configuration
    DATABASE_URI,
    # File upload configuration
    MAX_CONTENT_LENGTH,
)

# Configure the database using settings from config.py
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": DATABASE_POOL_RECYCLE,
    "pool_pre_ping": DATABASE_POOL_PRE_PING,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = DATABASE_TRACK_MODIFICATIONS

# Configure file uploads
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

# Initialize the database
db.init_app(app)

from routes.chat_routes import chat_bp
from routes.file_routes import file_bp
from routes.settings_routes import settings_bp
from services.agent_registry import ensure_default_agents
from services.settings_service import (
    ensure_default_ui_settings,
    get_general_settings,
    get_theme_settings,
    get_ui_settings,
    readiness,
)

app.register_blueprint(chat_bp)
app.register_blueprint(file_bp)
app.register_blueprint(settings_bp)

with app.app_context():
    db.create_all()
    try:
        import os

        db_path = None
        if DATABASE_URI.startswith("sqlite:///"):
            db_path = DATABASE_URI.replace("sqlite:///", "")
        size_bytes = os.path.getsize(db_path) if db_path and os.path.exists(db_path) else 0
        logger.info(
            f"Database tables created successfully. DB URI={DATABASE_URI} size={size_bytes} bytes"
        )
    except Exception as _exc:  # noqa: F841
        logger.info(f"Database tables created successfully. DB URI={DATABASE_URI}")
    # Seed default agents (safe no-op if already present)
    try:
        ensure_default_agents()
    except Exception as e:
        logger.warning(f"Could not seed default agents: {e}")


# Serve the main page
@app.route("/")
def index():
    # Ensure default UI settings exist for neutral rendering
    ensure_default_ui_settings()
    # First-run gating
    status = readiness()
    if not status.get("ready", False):
        return redirect(url_for("settings_page"))
    ui = get_ui_settings()
    general = get_general_settings()
    theme = get_theme_settings()
    return render_template(
        "index.html",
        brand_name=general.get("brand_name", "RAG Agent"),
        bot_welcome_message=ui.get("welcome_message", ""),
        predefined_prompts=json.dumps(ui.get("predefined_prompts", [])),
        default_course_thumbnail=ui.get(
            "default_course_thumbnail", "/static/images/course_thumbnail.svg"
        ),
        theme=theme,
    )


# Serve the files management page
@app.route("/files")
def files():
    ensure_default_ui_settings()
    general = get_general_settings()
    theme = get_theme_settings()
    return render_template(
        "files.html", brand_name=general.get("brand_name", "RAG Agent"), theme=theme
    )


# Simple settings page stub (first-run wizard placeholder)
@app.route("/settings")
def settings_page():
    ensure_default_ui_settings()
    general = get_general_settings()
    theme = get_theme_settings()
    # Render a minimal settings wizard; frontend can call /api/settings/* endpoints
    return render_template(
        "settings.html", brand_name=general.get("brand_name", "RAG Agent"), theme=theme
    )


# Import server config
from config import DEBUG_MODE, SERVER_HOST, SERVER_PORT

if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
