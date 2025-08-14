import os
import logging
from flask import Flask, render_template
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

# Import blueprints after db init to avoid circular imports
from routes.chat_routes import chat_bp
from routes.file_routes import file_bp

# Register blueprints
app.register_blueprint(chat_bp)
app.register_blueprint(file_bp)

# Create database tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created successfully")
    
    # Import file service here to avoid circular imports
    from services.file_service import scan_knowledge_base
    
    # Get document information from Pinecone on startup
    try:
        pinecone_info = scan_knowledge_base()
        if pinecone_info:
            stats = pinecone_info.get("pinecone_stats", {})
            logger.info(f"Pinecone contains {stats.get('total_chunks', 0)} chunks from {stats.get('unique_files', 0)} documents")
    except Exception as e:
        logger.error(f"Error retrieving Pinecone document information on startup: {str(e)}", exc_info=True)

# Serve the main page
@app.route('/')
def index():
    # Import configuration values to pass to the template
    from config import BOT_WELCOME_MESSAGE, PREDEFINED_PROMPTS_JSON, DEFAULT_COURSE_THUMBNAIL
    
    return render_template(
        'index.html',
        bot_welcome_message=BOT_WELCOME_MESSAGE,
        predefined_prompts=PREDEFINED_PROMPTS_JSON,
        default_course_thumbnail=DEFAULT_COURSE_THUMBNAIL
    )

# Serve the files management page
@app.route('/files')
def files():
    return render_template('files.html')

# Import server config
from config import SERVER_HOST, SERVER_PORT, DEBUG_MODE

if __name__ == '__main__':
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE)
