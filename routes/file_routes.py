import logging
import uuid

from flask import Blueprint, jsonify, render_template, request
from werkzeug.utils import secure_filename

from database import db
from services.file_service import (
    delete_file_by_id,
    extract_text_and_metadata,
    get_all_files,
    get_file_by_id,
    process_file_for_rag,
    save_file,
    scan_knowledge_base,
)
from services.settings_service import get_rag_settings

# Configure logging
logger = logging.getLogger(__name__)
# Logging is already configured in app.py
logger.debug("File routes logger configured")

# Create a Blueprint for file routes
file_bp = Blueprint("file_bp", __name__, url_prefix="/api")


def allowed_file(filename):
    """Check if the file extension is allowed"""
    allowed = set(
        get_rag_settings().get(
            "allowed_extensions", ["txt", "json", "md", "jsonl", "csv", "docx", "pdf", "xlsx"]
        )
    )
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


@file_bp.route("/files/upload", methods=["POST"])
def upload_file():
    """
    Upload a new file, process it, and add it to the RAG database
    """
    try:
        # Check if a file was included in the request
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]

        # Check if a file was selected
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Check if the file type is allowed
        if not allowed_file(file.filename):
            allowed = get_rag_settings().get(
                "allowed_extensions", ["txt", "json", "md", "jsonl", "csv", "docx", "pdf", "xlsx"]
            )
            return jsonify({"error": f'Unsupported file type. Allowed: {", ".join(allowed)}'}), 400

        # Create a secure filename
        filename = secure_filename(file.filename)

        # Generate a unique ID for the file
        file_id = str(uuid.uuid4())

        # Read the raw file bytes
        raw_bytes = file.read()

        # Get the file type
        file_type = filename.rsplit(".", 1)[1].lower()

        # Parse content and detect metadata
        try:
            parsed_text, meta = extract_text_and_metadata(file_type, raw_bytes)
        except ImportError as ie:
            logger.error(f"Missing dependency while parsing {filename}: {ie}")
            return (
                jsonify(
                    {
                        "error": f"Missing dependency for parsing {file_type.upper()} files. Please install required libraries and retry."
                    }
                ),
                400,
            )

        # Save the file (parsed text) with detected doc_type if present
        save_file(
            file_id,
            filename,
            file_type,
            parsed_text,
            detected_doc_type=(meta.get("doc_type") if isinstance(meta, dict) else None),
        )

        # Process the file for RAG
        process_file_for_rag(file_id, filename, parsed_text, file_type)

        return jsonify(
            {
                "success": True,
                "message": f"File {filename} has been uploaded and processed",
                "file_id": file_id,
            }
        )

    except Exception as e:
        # Ensure any database operations are rolled back on error
        db.session.rollback()

        # Log detailed error for debugging
        logger.error(f"Error in upload_file endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while uploading the file"}), 500


@file_bp.route("/files", methods=["GET"])
def get_files():
    """
    Get a list of all files
    """
    try:
        files = get_all_files()
        return jsonify({"files": files})

    except Exception as e:
        # Log the error with detailed information for troubleshooting
        logger.error(f"Error in get_files endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while retrieving files"}), 500


@file_bp.route("/files/<file_id>", methods=["GET"])
def get_file(file_id):
    """
    Get a specific file by ID
    """
    try:
        file, content = get_file_by_id(file_id)

        if not file:
            return jsonify({"error": "File not found"}), 404

        return jsonify({"file": file, "content": content})

    except Exception as e:
        # Log the error with detailed information for troubleshooting
        logger.error(f"Error in get_file endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while retrieving the file"}), 500


@file_bp.route("/files/<file_id>", methods=["DELETE"])
def delete_file(file_id):
    """
    Delete a specific file
    """
    try:
        success = delete_file_by_id(file_id)

        if not success:
            return jsonify({"error": "File not found"}), 404

        return jsonify({"success": True})

    except Exception as e:
        # Ensure any database operations are rolled back on error
        db.session.rollback()

        logger.error(f"Error in delete_file endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while deleting the file"}), 500


@file_bp.route("/files/all", methods=["DELETE"])
def delete_all_files():
    """
    Delete all files and their corresponding Pinecone data
    """
    try:
        # Get all files to delete them
        files = get_all_files()
        deleted_count = 0

        # Delete each file
        for file in files:
            if delete_file_by_id(file.get("id")):
                deleted_count += 1

        return jsonify(
            {
                "success": True,
                "message": f"{deleted_count} files have been deleted",
                "count": deleted_count,
            }
        )

    except Exception as e:
        # Ensure any database operations are rolled back on error
        db.session.rollback()

        logger.error(f"Error in delete_all_files endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An error occurred while deleting all files"}), 500


@file_bp.route("/files/sync", methods=["GET", "POST"])
def sync_knowledge_base():
    """
    Retrieve and display information about documents in Pinecone.
    This is a read-only operation that doesn't modify the database.
    """
    try:
        # Get document information from Pinecone
        pinecone_info = scan_knowledge_base()

        # Extract statistics
        total_chunks = pinecone_info["pinecone_stats"]["total_chunks"]
        unique_files = pinecone_info["pinecone_stats"]["unique_files"]

        return jsonify(
            {
                "success": True,
                "message": f"Pinecone contains {total_chunks} chunks from {unique_files} documents.",
                "stats": pinecone_info["pinecone_stats"],
                "documents": pinecone_info["pinecone_documents"],
            }
        )

    except Exception as e:
        logger.error(f"Error in sync_knowledge_base endpoint: {str(e)}", exc_info=True)
        return (
            jsonify({"error": "An error occurred while retrieving Pinecone document information"}),
            500,
        )


@file_bp.route("/files/page", methods=["GET"])
def files_page():
    """
    Render the files management page
    """
    return render_template("files.html")
