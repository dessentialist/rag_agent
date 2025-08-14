import os
import logging
from flask import Flask, render_template
import json
from database import db

# Import logging configuration
from config import LOG_LEVEL, LOG_FORMAT

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
    # Database configuration
    DATABASE_URI,
    DATABASE_POOL_RECYCLE,
    DATABASE_POOL_PRE_PING,
    DATABASE_TRACK_MODIFICATIONS,
    # File upload configuration
    MAX_CONTENT_LENGTH
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
from services.settings_service import ensure_default_ui_settings, get_ui_settings, get_general_settings, get_theme_settings
from services.agent_registry import ensure_default_agents

app.register_blueprint(chat_bp)
app.register_blueprint(file_bp)
app.register_blueprint(settings_bp)

with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")
    # Seed default agents (safe no-op if already present)
    try:
        ensure_default_agents()
    except Exception as e:
        logger.warning(f"Could not seed default agents: {e}")

# Serve the main page
@app.route('/')
def index():
    # Ensure default UI settings exist for neutral rendering
    ensure_default_ui_settings()
    ui = get_ui_settings()
    general = get_general_settings()
    theme = get_theme_settings()
    return render_template(
        'index.html',
        brand_name=general.get('brand_name', 'RAG Agent'),
        bot_welcome_message=ui.get('welcome_message', ''),
        predefined_prompts=json.dumps(ui.get('predefined_prompts', [])),
        default_course_thumbnail=ui.get('default_course_thumbnail', '/static/images/course_thumbnail.svg'),
        theme=theme,
    )

# Serve the files management page
@app.route('/files')
def files():
    ensure_default_ui_settings()
    general = get_general_settings()
    theme = get_theme_settings()
    return render_template('files.html', brand_name=general.get('brand_name', 'RAG Agent'), theme=theme)

# Import server config
from config import SERVER_HOST, SERVER_PORT, DEBUG_MODE

if __name__ == '__main__':
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
